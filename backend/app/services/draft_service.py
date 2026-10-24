"""Offline draft lifecycle with explicit states and verified submission only."""

from __future__ import annotations

import hashlib
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session as DbSession

from app.adapters.submission import get_submission_adapter
from app.db import ensure_aware, utcnow
from app.domain import DRAFT_STATE_LABELS, DRAFT_TRANSITIONS, DraftState
from app.models import (
    DraftVersion,
    Member,
    OfflineDraft,
    SubmissionAttempt,
    SubmissionReceipt,
    UserSession,
)
from app.security.access import get_household, require_member_access
from app.services.audit import record_audit


def _next_ref(db: DbSession) -> str:
    count = db.scalar(select(func.count()).select_from(OfflineDraft)) or 0
    return f"RS-D-{1042 + int(count)}"


def draft_out(draft: OfflineDraft) -> dict[str, Any]:
    return {
        "id": draft.id,
        "draft_ref": draft.draft_ref,
        "kind": draft.kind,
        "state": draft.state,
        "state_label": DRAFT_STATE_LABELS.get(draft.state, draft.state),
        "payload": draft.payload,
        "version": draft.version,
        "member_id": draft.member_id,
        "created_at": ensure_aware(draft.created_at).isoformat() if draft.created_at else None,
        "updated_at": ensure_aware(draft.updated_at).isoformat() if draft.updated_at else None,
        "last_error": draft.last_error,
        "official_receipt_id": draft.official_receipt_id,
        "is_official_submission": draft.state == DraftState.SUBMITTED_CONFIRMED,
        "notice": _notice(draft),
    }


def _notice(draft: OfflineDraft) -> str:
    if draft.state == DraftState.SUBMITTED_CONFIRMED:
        return "Submission confirmed by the configured adapter. Receipt verification is required before treating it as official."
    if draft.state == DraftState.SUBMISSION_PENDING_VERIFICATION:
        return "A response was received but no verified acknowledgement is available yet. Do not treat this as submitted."
    if draft.state == DraftState.SUBMISSION_FAILED:
        return "The draft has not been confirmed as submitted. You may retry when connected."
    if draft.state == DraftState.REQUIRES_REVIEW:
        return "This draft needs authorised review before it can be sent."
    return "Saved locally — not submitted to any official system."


def _transition(draft: OfflineDraft, new_state: str) -> None:
    allowed = DRAFT_TRANSITIONS.get(DraftState(draft.state), set())
    if DraftState(new_state) not in allowed:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Invalid draft state transition: {draft.state} -> {new_state}",
        )
    draft.state = new_state
    draft.updated_at = utcnow()


def create_draft(db: DbSession, session: UserSession, payload: dict[str, Any]) -> dict[str, Any]:
    household = get_household(db, session)
    member_id = payload.get("member_id") or session.member_id
    if member_id:
        member = db.get(Member, member_id)
        if member is None or member.household_id != household.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Member record not found")
        require_member_access(session, member)

    idempotency_key = payload.get("idempotency_key") or "draft-" + hashlib.sha256(
        f"{session.id}:{utcnow().isoformat()}:{payload.get('kind')}".encode()
    ).hexdigest()[:16]
    existing = db.scalar(select(OfflineDraft).where(OfflineDraft.idempotency_key == idempotency_key))
    if existing is not None:
        if existing.household_id != session.household_id:
            raise HTTPException(status.HTTP_409_CONFLICT, "This draft reference belongs to another household")
        return draft_out(existing)

    draft = OfflineDraft(
        draft_ref=_next_ref(db),
        household_id=household.id,
        member_id=member_id,
        kind=payload.get("kind", "CORRECTION"),
        state=DraftState.DRAFT_NOT_SUBMITTED,
        payload=payload.get("payload") or {},
        idempotency_key=idempotency_key,
        created_by_session=session.id,
    )
    db.add(draft)
    db.flush()
    db.add(DraftVersion(draft_id=draft.id, version=1, payload=draft.payload))
    record_audit(
        db,
        action="draft_created",
        session=session,
        household_ref=household.reference,
        member_ref=member_id,
        entity_type="offline_draft",
        entity_id=draft.id,
        detail={"kind": draft.kind, "draft_ref": draft.draft_ref},
    )
    db.flush()
    return draft_out(draft)


def _get_draft(db: DbSession, session: UserSession, draft_id: str) -> OfflineDraft:
    draft = db.get(OfflineDraft, draft_id)
    if draft is None or draft.household_id != session.household_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Draft not found")
    if draft.member_id:
        member = db.get(Member, draft.member_id)
        if member is not None:
            require_member_access(session, member)
    return draft


def list_drafts(db: DbSession, session: UserSession) -> list[dict[str, Any]]:
    query = select(OfflineDraft).where(OfflineDraft.household_id == session.household_id)
    if session.role == "MEMBER":
        query = query.where(
            (OfflineDraft.member_id == session.member_id) | (OfflineDraft.member_id.is_(None))
        )
    elif session.role == "FACILITATOR":
        if session.member_id is None:
            return []
        query = query.where(OfflineDraft.member_id == session.member_id)
    else:
        return []
    drafts = db.scalars(query.order_by(OfflineDraft.created_at.desc())).all()
    return [draft_out(d) for d in drafts]


def update_draft(db: DbSession, session: UserSession, draft_id: str, payload: dict[str, Any], expected_version: int) -> dict[str, Any]:
    draft = _get_draft(db, session, draft_id)
    if draft.state == DraftState.SUBMITTED_CONFIRMED:
        raise HTTPException(status.HTTP_409_CONFLICT, "A confirmed submission cannot be edited")
    if draft.version != expected_version:
        raise HTTPException(status.HTTP_409_CONFLICT, "This draft was updated elsewhere. Reload before editing.")
    draft.payload = payload
    draft.version += 1
    draft.updated_at = utcnow()
    db.add(draft)
    db.add(DraftVersion(draft_id=draft.id, version=draft.version, payload=payload))
    db.flush()
    return draft_out(draft)


def sync_draft(db: DbSession, session: UserSession, draft_id: str, network_online: bool) -> dict[str, Any]:
    draft = _get_draft(db, session, draft_id)
    household = get_household(db, session)

    if draft.state == DraftState.SUBMITTED_CONFIRMED:
        return {
            **draft_out(draft),
            "synced": True,
            "official_submission_confirmed": True,
            "message": "This draft already has a verified simulated acknowledgement. No duplicate submission was made.",
        }
    if draft.state == DraftState.SUBMISSION_PENDING_VERIFICATION:
        return {
            **draft_out(draft),
            "synced": True,
            "official_submission_confirmed": False,
            "message": "Data was already sent. Waiting for a verified acknowledgement; retrying will not duplicate the submission.",
        }
    if not network_online:
        _transition(draft, DraftState.QUEUED_FOR_SYNC)
        db.add(draft)
        db.commit()
        return {
            **draft_out(draft),
            "synced": False,
            "official_submission_confirmed": False,
            "message": "Waiting for a connection. Nothing has been sent and nothing is confirmed as submitted.",
        }

    if draft.state in {DraftState.DRAFT_NOT_SUBMITTED, DraftState.SUBMISSION_FAILED}:
        _transition(draft, DraftState.QUEUED_FOR_SYNC)
    if draft.state == DraftState.QUEUED_FOR_SYNC:
        _transition(draft, DraftState.SYNC_IN_PROGRESS)
    if draft.state == DraftState.SYNC_IN_PROGRESS:
        _transition(draft, DraftState.SUBMISSION_PENDING_VERIFICATION)

    attempt_key = f"draft-sync-{draft.id}-v{draft.version}"
    existing_attempt = db.scalar(select(SubmissionAttempt).where(SubmissionAttempt.idempotency_key == attempt_key))
    if existing_attempt is None:
        db.add(
            SubmissionAttempt(
                draft_id=draft.id,
                idempotency_key=attempt_key,
                adapter="SIMULATED_TRANSPORT",
                outcome="PENDING_VERIFICATION",
                request_fingerprint=hashlib.sha256(attempt_key.encode()).hexdigest(),
                response={
                    "transport_status": "received_by_simulated_transport",
                    "official_acknowledgement": False,
                    "note": "Transport success is not proof of official submission.",
                },
            )
        )
    draft.updated_at = utcnow()
    db.add(draft)
    record_audit(
        db,
        action="draft_synced",
        session=session,
        household_ref=household.reference,
        member_ref=draft.member_id,
        entity_type="offline_draft",
        entity_id=draft.id,
        detail={"state": draft.state, "attempt": attempt_key},
    )
    db.flush()
    return {
        **draft_out(draft),
        "synced": True,
        "official_submission_confirmed": False,
        "message": "Draft data was sent. Official submission is not confirmed until a verified acknowledgement is processed.",
    }


def verify_submission(db: DbSession, session: UserSession, draft_id: str, simulate_receipt: bool) -> dict[str, Any]:
    draft = _get_draft(db, session, draft_id)
    household = get_household(db, session)
    existing_receipt = db.scalar(select(SubmissionReceipt).where(SubmissionReceipt.draft_id == draft.id))
    if existing_receipt is not None:
        return {
            **draft_out(draft),
            "verified": True,
            "receipt": {
                "receipt_number": existing_receipt.receipt_number,
                "is_simulated": existing_receipt.is_simulated,
                "verified": existing_receipt.verified,
                "adapter": existing_receipt.adapter,
            },
            "message": "Existing verified acknowledgement reused. No duplicate submission was made.",
        }

    if draft.state != DraftState.SUBMISSION_PENDING_VERIFICATION:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "No pending submission to verify. Sync the draft before checking for an acknowledgement.",
        )
    if not simulate_receipt:
        return {
            **draft_out(draft),
            "verified": False,
            "receipt": None,
            "message": "No verified acknowledgement is available. The draft is not confirmed as submitted.",
        }

    adapter = get_submission_adapter()
    attempt_key = f"draft-verify-{draft.id}-v{draft.version}"
    result = adapter.submit(draft_ref=draft.draft_ref, payload=draft.payload, idempotency_key=attempt_key)
    db.add(
        SubmissionAttempt(
            draft_id=draft.id,
            idempotency_key=attempt_key,
            adapter=adapter.name,
            outcome="ACCEPTED" if result.accepted else "FAILED",
            request_fingerprint=hashlib.sha256(attempt_key.encode()).hexdigest(),
            response=result.raw,
        )
    )
    if not (result.accepted and result.verified and result.receipt_number):
        draft.last_error = result.message
        db.add(draft)
        db.flush()
        return {
            **draft_out(draft),
            "verified": False,
            "receipt": None,
            "message": result.message,
        }

    receipt = SubmissionReceipt(
        draft_id=draft.id,
        receipt_number=result.receipt_number,
        adapter=adapter.name,
        is_simulated=result.is_simulated,
        verified=True,
        issued_at=result.issued_at,
        verified_at=utcnow(),
        raw=result.raw,
    )
    db.add(receipt)
    db.flush()
    _transition(draft, DraftState.SUBMITTED_CONFIRMED)
    draft.official_receipt_id = receipt.id
    db.add(draft)
    record_audit(
        db,
        action="submission_verified",
        session=session,
        household_ref=household.reference,
        member_ref=draft.member_id,
        entity_type="offline_draft",
        entity_id=draft.id,
        detail={"adapter": adapter.name, "simulated": True, "receipt_id": receipt.id},
    )
    db.flush()
    return {
        **draft_out(draft),
        "verified": True,
        "receipt": {
            "receipt_number": receipt.receipt_number,
            "is_simulated": True,
            "verified": True,
            "adapter": adapter.name,
            "message": result.message,
        },
        "message": "SIMULATED submission confirmed. This is not an official government receipt.",
    }


def cancel_draft(db: DbSession, session: UserSession, draft_id: str) -> dict[str, Any]:
    draft = _get_draft(db, session, draft_id)
    if draft.state == DraftState.SUBMITTED_CONFIRMED:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "A confirmed submission cannot be deleted here. It is the only link to the acknowledgement.",
        )
    if draft.state != DraftState.CANCELLED:
        _transition(draft, DraftState.CANCELLED)
    # Remove sensitive form content; keep a non-sensitive audit trail.
    draft.payload = {"cleared": True, "label": "DRAFT — CANCELLED", "previous_kind": draft.kind}
    draft.updated_at = utcnow()
    db.add(draft)
    record_audit(
        db,
        action="draft_cleared",
        session=session,
        household_ref=session.household_id,
        member_ref=draft.member_id,
        entity_type="offline_draft",
        entity_id=draft.id,
        detail={"state": "CANCELLED"},
    )
    db.flush()
    return draft_out(draft)
