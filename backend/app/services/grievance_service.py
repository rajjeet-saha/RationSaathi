"""Grievance lifecycle, deadline verification and privacy-preserving escalation."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.adapters.submission import get_submission_adapter
from app.db import ensure_aware, utcnow
from app.domain import GrievanceStatus, Provenance
from app.models import (
    EscalationDraft,
    Grievance,
    GrievanceEvent,
    Member,
    ServiceLevelPolicy,
    UserSession,
)
from app.services.audit import record_audit


def _fmt_date(value: datetime | None) -> str:
    return ensure_aware(value).strftime("%d %B %Y") if value else "Not verified"


def effective_status(db: DbSession, grievance: Grievance, now: datetime | None = None) -> tuple[str, dict[str, Any]]:
    """OVERDUE only when a configured deadline is verified and has passed."""
    now = now or utcnow()
    filed = ensure_aware(grievance.filed_at)
    deadline = ensure_aware(grievance.deadline_at)
    policy = db.get(ServiceLevelPolicy, grievance.sla_policy_id) if grievance.sla_policy_id else None

    metadata = {
        "deadline_verified": grievance.deadline_verified,
        "deadline_at": deadline.isoformat() if deadline else None,
        "deadline_label": _fmt_date(deadline) if deadline else None,
        "policy": (
            {
                "version": policy.version,
                "days": policy.days,
                "source_label": policy.source_label,
                "verified": policy.verified,
                "is_synthetic": policy.is_synthetic,
            }
            if policy
            else None
        ),
        "filed_days_ago": max((now - filed).days, 0) if filed else None,
    }

    if not grievance.deadline_verified or deadline is None:
        metadata["deadline_note"] = "Deadline not verified — check the applicable service standard."
        metadata["overdue"] = False
        return grievance.status, metadata

    has_response = bool(grievance.response_summary) or grievance.status in {
        GrievanceStatus.RESOLVED,
        GrievanceStatus.ESCALATED,
    }
    if not has_response and now > deadline:
        metadata["overdue"] = True
        metadata["deadline_note"] = (
            "The configured service deadline has passed with no recorded response. "
            "This is based on a synthetic SLA fixture, not a legal determination."
        )
        return GrievanceStatus.OVERDUE, metadata

    metadata["overdue"] = False
    metadata["deadline_note"] = "Configured service deadline has not passed, or a qualifying response is recorded."
    return grievance.status, metadata


def grievance_out(db: DbSession, grievance: Grievance, now: datetime | None = None) -> dict[str, Any]:
    resolved_status, meta = effective_status(db, grievance, now)
    return {
        "id": grievance.id,
        "category": grievance.category,
        "subject": grievance.subject,
        "filed_at": ensure_aware(grievance.filed_at).isoformat() if grievance.filed_at else None,
        "provenance": grievance.provenance,
        "official_receipt_number": grievance.official_receipt_number,
        "local_draft_ref": grievance.local_draft_ref,
        "responsible_office": grievance.responsible_office,
        "office_verified": grievance.office_verified,
        "ownership": (
            grievance.responsible_office
            if grievance.office_verified
            else "Needs verification — identify the responsible office from the verified receipt or the receiving office"
        ),
        "assigned_officer": grievance.assigned_officer,
        "status": resolved_status,
        "stored_status": grievance.status,
        "last_status_update": ensure_aware(grievance.last_status_update).isoformat()
        if grievance.last_status_update
        else None,
        "response_recorded": bool(grievance.response_summary),
        "response_summary": grievance.response_summary,
        "resolution_summary": grievance.resolution_summary,
        "deadline": meta,
        "is_synthetic": grievance.is_synthetic,
        "disclaimer": "Synthetic grievance fixture. No official government case is represented.",
    }


def _accessible_member(db: DbSession, session: UserSession, grievance: Grievance) -> Member | None:
    if grievance.member_id:
        return db.get(Member, grievance.member_id)
    return None


def _check_scope(session: UserSession, grievance: Grievance) -> None:
    if grievance.household_id != session.household_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Grievance not found")
    if session.role == "MEMBER" and grievance.member_id not in {None, session.member_id}:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This grievance belongs to another member")
    if session.role == "FACILITATOR" and grievance.member_id != session.member_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This grievance is outside the consented profile scope")


def list_grievances(db: DbSession, session: UserSession) -> list[dict[str, Any]]:
    grievances = db.scalars(
        select(Grievance).where(Grievance.household_id == session.household_id).order_by(Grievance.filed_at.desc())
    ).all()
    visible: list[dict[str, Any]] = []
    for grievance in grievances:
        try:
            _check_scope(session, grievance)
        except HTTPException:
            continue
        visible.append(grievance_out(db, grievance))
    return visible


def get_grievance(db: DbSession, session: UserSession, grievance_id: str) -> Grievance:
    grievance = db.get(Grievance, grievance_id)
    if grievance is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Grievance not found")
    _check_scope(session, grievance)
    if session.role == "FACILITATOR" and grievance.member_id not in (session.consent_member_ids or []):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Consent is required before viewing this grievance")
    return grievance


def detail(db: DbSession, session: UserSession, grievance_id: str) -> dict[str, Any]:
    grievance = get_grievance(db, session, grievance_id)
    events = db.scalars(
        select(GrievanceEvent)
        .where(GrievanceEvent.grievance_id == grievance.id)
        .order_by(GrievanceEvent.occurred_at.asc())
    ).all()
    escalations = db.scalars(
        select(EscalationDraft)
        .where(EscalationDraft.grievance_id == grievance.id)
        .order_by(EscalationDraft.created_at.desc())
    ).all()
    return {
        **grievance_out(db, grievance),
        "events": [
            {
                "event_type": event.event_type,
                "occurred_at": ensure_aware(event.occurred_at).isoformat(),
                "detail": event.detail,
            }
            for event in events
        ],
        "escalations": [
            {
                "id": esc.id,
                "state": esc.state,
                "body": esc.body,
                "created_at": ensure_aware(esc.created_at).isoformat(),
                "submitted_receipt": esc.submitted_receipt,
            }
            for esc in escalations
        ],
    }


def _escalation_body(grievance: Grievance, meta: dict[str, Any], *, officer: str | None, office: str | None,
                     contact: str | None) -> str:
    receipt = grievance.official_receipt_number or "[Official receipt not verified — do not invent a number]"
    deadline = meta.get("deadline_label") if meta.get("deadline_verified") else "[Verified service deadline not available]"
    lines = [
        "Subject: Request for a status update and identification of the responsible office",
        "",
        f"Responsible officer: {officer or '[Responsible officer — not verified]'}",
        f"Responsible office: {office or '[Responsible office — not verified; please route this request]'}",
        f"Official grievance receipt: {receipt}",
        f"Filing date: {_fmt_date(grievance.filed_at)}",
        f"Service deadline: {deadline}",
        f"Current recorded status: {grievance.status}",
        "",
        "I am writing about the grievance referenced above. I would like to request:",
        "1. Confirmation of the current status of this grievance.",
        "2. Identification of the office and officer responsible for the next step.",
        "3. An explanation of any information or evidence still required from the household.",
        "4. A clear indication of what action I can take next, and by when a response may be expected.",
        "",
    ]
    if not meta.get("deadline_verified"):
        lines.append(
            "No verified service deadline is available to me for this case. I am not asserting that any statutory "
            "deadline has passed; I am asking for the applicable service standard to be confirmed."
        )
    elif meta.get("overdue"):
        lines.append(
            "According to the configured service standard provided to me, the expected response period has passed. "
            "I am requesting a status update and an explanation of the next step, not a legal finding."
        )
    else:
        lines.append(
            "I understand that the configured response period may not yet have ended. I am requesting a status update."
        )
    lines += [
        "",
        "Please do not include identity-document numbers in any reply. A safe contact method is:",
        f"{contact or '[Safe contact method — provide a shared or facilitated contact, not the private number of another member]'}",
        "",
        "This escalation draft was prepared with RationSaathi. It is not yet an official submission until it is sent "
        "through an authorised channel and a receipt is verified.",
        "",
        "[Household signature placeholder]",
    ]
    return "\n".join(lines)


def list_events(db: DbSession, grievance_id: str) -> list[dict[str, Any]]:
    events = db.scalars(
        select(GrievanceEvent).where(GrievanceEvent.grievance_id == grievance_id).order_by(GrievanceEvent.occurred_at)
    ).all()
    return [
        {
            "event_type": e.event_type,
            "occurred_at": ensure_aware(e.occurred_at).isoformat(),
            "detail": e.detail,
        }
        for e in events
    ]


def refresh_status(db: DbSession, session: UserSession, grievance_id: str) -> dict[str, Any]:
    grievance = get_grievance(db, session, grievance_id)
    resolved, meta = effective_status(db, grievance, utcnow())
    if resolved != grievance.status and resolved == GrievanceStatus.OVERDUE:
        grievance.status = resolved
        grievance.last_status_update = utcnow()
        db.add(grievance)
        db.add(
            GrievanceEvent(
                grievance_id=grievance.id,
                event_type="STATUS_RECALCULATED_OVERDUE",
                detail={
                    "policy_verified": True,
                    "source": meta.get("policy", {}).get("source_label") if meta.get("policy") else None,
                    "note": "Derived from a synthetic configured deadline, not a legal determination.",
                },
            )
        )
        record_audit(
            db,
            action="grievance_status_recalculated",
            session=session,
            household_ref=session.household_id,
            member_ref=grievance.member_id,
            entity_type="grievance",
            entity_id=grievance.id,
            detail={"status": resolved},
        )
        db.flush()
    return {**grievance_out(db, grievance), "events": list_events(db, grievance.id)}


def create_escalation(
    db: DbSession,
    session: UserSession,
    grievance_id: str,
    *,
    recipient_office: str | None,
    officer_placeholder: str | None,
    safe_contact: str | None,
    body: str | None,
) -> dict[str, Any]:
    grievance = get_grievance(db, session, grievance_id)
    _, meta = effective_status(db, grievance, utcnow())
    text = body or _escalation_body(
        grievance,
        meta,
        officer=officer_placeholder,
        office=recipient_office or grievance.responsible_office,
        contact=safe_contact,
    )
    draft = EscalationDraft(
        grievance_id=grievance.id,
        body=text,
        state="DRAFT_NOT_SUBMITTED",
        created_by_session=session.id,
    )
    db.add(draft)
    if grievance.status not in {GrievanceStatus.RESOLVED, GrievanceStatus.ESCALATED}:
        grievance.status = GrievanceStatus.ESCALATION_DRAFT
        db.add(grievance)
    db.add(
        GrievanceEvent(
            grievance_id=grievance.id,
            event_type="ESCALATION_DRAFT_CREATED",
            detail={"deadline_verified": meta.get("deadline_verified", False), "state": draft.state},
        )
    )
    record_audit(
        db,
        action="escalation_prepared",
        session=session,
        household_ref=session.household_id,
        member_ref=grievance.member_id,
        entity_type="grievance",
        entity_id=grievance.id,
        detail={"deadline_verified": meta.get("deadline_verified", False)},
    )
    db.flush()
    return {
        "id": draft.id,
        "grievance_id": grievance.id,
        "body": draft.body,
        "state": draft.state,
        "state_label": "DRAFT — NOT SUBMITTED",
        "deadline_verified": meta.get("deadline_verified", False),
        "deadline_note": meta.get("deadline_note"),
        "placeholders": {
            "official_receipt": grievance.official_receipt_number,
            "responsible_officer": officer_placeholder,
            "responsible_office": recipient_office or grievance.responsible_office,
            "filing_date": _fmt_date(grievance.filed_at),
            "service_deadline": meta.get("deadline_label") if meta.get("deadline_verified") else None,
            "safe_contact": safe_contact,
        },
        "notice": "This is a draft. It is not a filed grievance and must be sent through an authorised channel.",
    }


def update_escalation(db: DbSession, session: UserSession, escalation_id: str, body: str) -> dict[str, Any]:
    draft = db.get(EscalationDraft, escalation_id)
    if draft is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Escalation draft not found")
    get_grievance(db, session, draft.grievance_id)
    if draft.state == "SUBMITTED_CONFIRMED":
        raise HTTPException(status.HTTP_409_CONFLICT, "A submitted escalation cannot be edited")
    draft.body = body
    db.add(draft)
    db.flush()
    return {"id": draft.id, "body": draft.body, "state": draft.state, "state_label": "DRAFT — NOT SUBMITTED"}


def submit_escalation(
    db: DbSession, session: UserSession, escalation_id: str, *, confirm_authorised_channel: bool
) -> dict[str, Any]:
    draft = db.get(EscalationDraft, escalation_id)
    if draft is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Escalation draft not found")
    grievance = get_grievance(db, session, draft.grievance_id)
    if not confirm_authorised_channel:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Confirm that the escalation will be sent through an authorised channel before submitting",
        )
    if draft.state == "SUBMITTED_CONFIRMED":
        raise HTTPException(status.HTTP_409_CONFLICT, "This escalation already has a verified acknowledgement")
    if not grievance.official_receipt_number:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "The original grievance has no verified receipt. Verify the original filing before escalating.",
        )
    if not grievance.office_verified:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "The responsible office is not verified. Confirm ownership before submitting.",
        )
    adapter = get_submission_adapter()
    result = adapter.submit(
        draft_ref=f"ESC-{draft.id[:8]}",
        payload={"grievance_id": grievance.id},
        idempotency_key=f"escalation-{draft.id}",
    )
    if not (result.accepted and result.receipt_number and result.verified):
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "The configured adapter did not verify the submission")
    draft.state = "SUBMITTED_CONFIRMED"
    draft.submitted_receipt = {
        "receipt_number": result.receipt_number,
        "is_simulated": True,
        "verified": True,
        "adapter": result.adapter,
        "message": result.message,
    }
    grievance.status = GrievanceStatus.ESCALATED
    grievance.last_status_update = utcnow()
    db.add(draft)
    db.add(grievance)
    db.add(
        GrievanceEvent(
            grievance_id=grievance.id,
            event_type="ESCALATED_SIMULATED",
            detail={"receipt_number": result.receipt_number, "simulated": True},
        )
    )
    record_audit(
        db,
        action="escalation_submitted_simulated",
        session=session,
        household_ref=session.household_id,
        member_ref=grievance.member_id,
        entity_type="grievance",
        entity_id=grievance.id,
        detail={"adapter": result.adapter, "simulated": True},
    )
    db.flush()
    return {
        "escalation": {
            "id": draft.id,
            "state": draft.state,
            "body": draft.body,
            "submitted_receipt": draft.submitted_receipt,
        },
        "grievance": grievance_out(db, grievance),
        "message": result.message,
    }
