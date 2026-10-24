"""Correction simulation service: persistence, authorisation and submission."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session as DbSession

from app.adapters.submission import get_submission_adapter
from app.db import utcnow
from app.domain import CorrectionOperation, ProposalStatus, RiskLevel
from app.models import (
    CorrectionProposal,
    CorrectionRiskFindingRow,
    EvidenceChecklist,
    Household,
    Member,
    OfflineDraft,
    RecordSnapshot,
    SubmissionAttempt,
    SubmissionReceipt,
    UserSession,
)
from app.rules.correction import (
    ActorContext,
    CorrectionSimulation,
    EntitlementFact,
    HouseholdFact,
    MemberFact,
    ProposedChange,
    simulate_correction,
)
from app.schemas import CorrectionSimulateRequest
from app.security.access import actor_capabilities, require_member_access, require_self_or_authorised
from app.services.audit import record_audit


def build_fact(household: Household) -> HouseholdFact:
    members = tuple(
        MemberFact(
            id=m.id,
            alias=m.display_alias,
            name=m.full_name,
            age=m.age,
            membership_status=m.membership_status,
            is_head=m.is_head,
            is_dependent=m.is_dependent,
            document_name=m.document_name,
            document_age=m.document_age,
            document_ref=m.document_ref,
            entitlements=tuple(
                EntitlementFact(
                    id=e.id,
                    commodity_code=e.commodity_code,
                    period=e.period,
                    entitled_qty=e.entitled_qty,
                    drawn_qty=e.drawn_qty,
                    remaining_qty=e.remaining_qty,
                    provenance=e.provenance,
                )
                for e in m.entitlements
            ),
        )
        for m in household.members
    )
    return HouseholdFact(id=household.id, reference=household.reference, members=members)


def _redact_snapshot(snapshot: dict[str, Any], visible_member_id: str) -> dict[str, Any]:
    """Only the selected member's values may leave the API.

    Counts remain visible because they are needed to explain household-level
    impact, but other members are reduced to a non-identifying placeholder.
    """
    redacted = dict(snapshot)
    members = []
    hidden_index = 0
    for member in snapshot.get("members", []):
        if member.get("member_id") == visible_member_id:
            members.append(member)
        else:
            hidden_index += 1
            members.append(
                {
                    "member_id": f"restricted-{hidden_index}",
                    "alias": "Another household member (hidden)",
                    "name": None,
                    "age": None,
                    "membership_status": "HIDDEN",
                    "is_head": False,
                    "is_dependent": False,
                    "document_name": None,
                    "document_age": None,
                    "document_ref_present": False,
                    "entitlement_links": [],
                    "hidden": True,
                }
            )
    redacted["members"] = members
    redacted["redaction_note"] = "Other members' values are hidden in this session."
    return redacted


def _serialise(proposal: CorrectionProposal, visible_member_id: str | None = None) -> dict[str, Any]:
    return {
        "proposal_id": proposal.id,
        "household_id": proposal.household_id,
        "member_id": proposal.member_id,
        "operation": proposal.operation,
        "status": proposal.status,
        "risk_level": proposal.risk_level,
        "blocked": proposal.blocked,
        "requires_review": proposal.requires_review,
        "safe_to_submit": (not proposal.blocked) and proposal.risk_level == RiskLevel.LOW,
        "findings": proposal.findings,
        "evidence": proposal.evidence,
        "before": _redact_snapshot(proposal.before_snapshot, visible_member_id or proposal.member_id),
        "after": _redact_snapshot(proposal.after_snapshot, visible_member_id or proposal.member_id),
        "rule_version": proposal.rule_version,
        "created_at": proposal.created_at.isoformat(),
        "submitted_at": proposal.submitted_at.isoformat() if proposal.submitted_at else None,
        "submission_receipt": proposal.submission_receipt,
        "label": "Simulation only — no official record has been changed.",
    }


def simulate(
    db: DbSession,
    *,
    session: UserSession,
    household: Household,
    request: CorrectionSimulateRequest,
) -> dict[str, Any]:
    target = db.get(Member, request.member_id)
    if target is None or target.household_id != household.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Member record not found")
    require_member_access(session, target)

    # Identity edits are limited to the member's own self-service session.
    if session.role == "MEMBER" and session.member_id != target.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Identity changes for another member require authorised review")

    capabilities = actor_capabilities(session)
    actor = ActorContext(
        role=session.role,
        session_member_id=session.member_id,
        can_change_identity=capabilities["can_change_identity"],
        can_change_membership=capabilities["can_change_membership"],
        consent_recorded=target.id in (session.consent_member_ids or []),
        head_absent=any(m.is_head and m.is_absent for m in household.members),
    )
    house = build_fact(household)

    snapshot = RecordSnapshot(
        household_id=household.id,
        member_id=target.id,
        reason="PRE_CORRECTION_SNAPSHOT",
        payload={"household_ref": household.reference, "member_state": house.members and _member_payload(house, target.id)},
    )
    db.add(snapshot)

    simulation: CorrectionSimulation = simulate_correction(
        house,
        ProposedChange(
            operation=request.operation,
            member_id=request.member_id,
            fields=request.fields,
            new_member=request.new_member,
            merge_into_member_id=request.merge_into_member_id,
            reason=request.reason,
        ),
        actor,
        evidence=request.evidence,
        rules_version="synthetic-correction-2026.1",
    )

    if simulation.blocked:
        proposal_status = ProposalStatus.BLOCKED
    elif simulation.risk_level == RiskLevel.HIGH:
        proposal_status = ProposalStatus.NEEDS_REVIEW
    elif simulation.requires_review:
        proposal_status = ProposalStatus.NEEDS_REVIEW
    else:
        proposal_status = ProposalStatus.SIMULATED

    proposal = CorrectionProposal(
        household_id=household.id,
        member_id=target.id,
        operation=request.operation,
        request_payload=request.model_dump(),
        status=str(proposal_status),
        risk_level=simulation.risk_level,
        blocked=simulation.blocked,
        requires_review=simulation.requires_review,
        before_snapshot=simulation.before,
        after_snapshot=simulation.after,
        findings=simulation.findings,
        evidence=simulation.evidence_checklist,
        rule_version="synthetic-correction-2026.1",
        created_by_session=session.id,
    )
    db.add(proposal)
    db.flush()

    for finding in simulation.findings:
        db.add(
            CorrectionRiskFindingRow(
                proposal_id=proposal.id,
                code=finding["code"],
                severity=finding["severity"],
                message=finding["message"],
                member_ref=finding.get("member_ref"),
                entitlement_ref=finding.get("entitlement_ref"),
                blocking=bool(finding.get("blocking")),
            )
        )
    db.add(EvidenceChecklist(proposal_id=proposal.id, items=simulation.evidence_checklist))

    record_audit(
        db,
        action="correction_simulated",
        session=session,
        household_ref=household.reference,
        member_ref=target.id,
        entity_type="correction_proposal",
        entity_id=proposal.id,
        outcome="BLOCKED" if simulation.blocked else simulation.risk_level,
        detail={
            "operation": request.operation,
            "risk_level": simulation.risk_level,
            "blocked": simulation.blocked,
            "member_count_before": simulation.diff["member_count_before"],
            "member_count_after": simulation.diff["member_count_after"],
            "entitlement_links_removed": len(simulation.diff["entitlement_links_removed"]),
        },
    )
    if simulation.blocked:
        record_audit(
            db,
            action="correction_blocked",
            session=session,
            household_ref=household.reference,
            member_ref=target.id,
            entity_type="correction_proposal",
            entity_id=proposal.id,
            outcome="BLOCKED",
            detail={"codes": [f["code"] for f in simulation.findings if f.get("blocking")]},
        )
    db.flush()
    payload = _serialise(proposal, target.id)
    payload["summary"] = simulation.summary
    payload["recommended_action"] = simulation.recommended_action
    payload["diff"] = simulation.diff
    return payload


def _member_payload(house: HouseholdFact, member_id: str) -> dict[str, Any] | None:
    for member in house.members:
        if member.id == member_id:
            return {
                "id": member.id,
                "alias": member.alias,
                "name": member.name,
                "age": member.age,
                "entitlements": [
                    {"id": e.id, "commodity": e.commodity_code, "period": e.period, "drawn_qty": e.drawn_qty}
                    for e in member.entitlements
                ],
            }
    return None


def get_proposal(db: DbSession, session: UserSession, proposal_id: str) -> CorrectionProposal:
    proposal = db.get(CorrectionProposal, proposal_id)
    if proposal is None or proposal.household_id != session.household_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Correction proposal not found")
    member = db.get(Member, proposal.member_id)
    if member is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Correction proposal not found")
    require_member_access(session, member)
    return proposal


def _next_draft_ref(db: DbSession) -> str:
    count = db.scalar(select(func.count()).select_from(OfflineDraft)) or 0
    return f"RS-D-{1042 + int(count)}"


def save_draft(
    db: DbSession,
    *,
    session: UserSession,
    household: Household,
    proposal_id: str,
    note: str | None,
) -> dict[str, Any]:
    proposal = get_proposal(db, session, proposal_id)
    if proposal.blocked:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "This destructive proposal cannot be saved for submission. The original record has been preserved.",
        )
    proposal.status = str(ProposalStatus.SAVED_DRAFT)
    draft = OfflineDraft(
        draft_ref=_next_draft_ref(db),
        household_id=household.id,
        member_id=proposal.member_id,
        kind="CORRECTION",
        state="DRAFT_NOT_SUBMITTED",
        payload={
            "proposal_id": proposal.id,
            "operation": proposal.operation,
            "risk_level": proposal.risk_level,
            "note": note,
            "label": "DRAFT — NOT SUBMITTED",
        },
        idempotency_key=f"correction-{proposal.id}",
        created_by_session=session.id,
    )
    db.add(draft)
    db.add(proposal)
    record_audit(
        db,
        action="correction_draft_created",
        session=session,
        household_ref=household.reference,
        member_ref=proposal.member_id,
        entity_type="offline_draft",
        entity_id=draft.id,
        detail={"risk_level": proposal.risk_level, "proposal_id": proposal.id},
    )
    db.flush()
    return {
        "proposal": _serialise(proposal, proposal.member_id),
        "draft_ref": draft.draft_ref,
        "draft_id": draft.id,
        "state": draft.state,
    }


def submit(
    db: DbSession,
    *,
    session: UserSession,
    household: Household,
    proposal_id: str,
) -> dict[str, Any]:
    proposal = get_proposal(db, session, proposal_id)
    target = db.get(Member, proposal.member_id)
    if target is not None and session.role == "MEMBER":
        require_self_or_authorised(session, target.id)

    if proposal.blocked:
        record_audit(
            db,
            action="correction_submission_rejected",
            session=session,
            household_ref=household.reference,
            member_ref=proposal.member_id,
            entity_type="correction_proposal",
            entity_id=proposal.id,
            outcome="REJECTED",
            detail={"reason": "BLOCKED_PROPOSAL"},
        )
        db.flush()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Blocked proposals cannot be submitted. Preserve the original record and seek authorised reconciliation.",
        )
    if proposal.risk_level != RiskLevel.LOW or proposal.requires_review:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "This proposal requires authorised human review before any submission.",
        )
    if proposal.submitted_at is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "This proposal has already been submitted")

    adapter = get_submission_adapter()
    now = utcnow()
    draft = OfflineDraft(
        draft_ref=_next_draft_ref(db),
        household_id=household.id,
        member_id=proposal.member_id,
        kind="CORRECTION",
        state="SUBMISSION_PENDING_VERIFICATION",
        payload={"proposal_id": proposal.id, "operation": proposal.operation},
        idempotency_key=f"submit-{proposal.id}",
        created_by_session=session.id,
    )
    db.add(draft)
    db.flush()

    attempt_key = f"correction-submit-{proposal.id}"
    result = adapter.submit(draft_ref=draft.draft_ref, payload=draft.payload, idempotency_key=attempt_key)
    db.add(
        SubmissionAttempt(
            draft_id=draft.id,
            idempotency_key=attempt_key,
            adapter=adapter.name,
            outcome="ACCEPTED" if result.accepted else "FAILED",
            request_fingerprint=attempt_key,
            response=result.raw,
        )
    )

    receipt_payload = None
    if result.accepted and result.verified and result.receipt_number:
        receipt = SubmissionReceipt(
            draft_id=draft.id,
            receipt_number=result.receipt_number,
            adapter=adapter.name,
            is_simulated=result.is_simulated,
            verified=True,
            issued_at=result.issued_at,
            verified_at=now,
            raw=result.raw,
        )
        db.add(receipt)
        db.flush()
        draft.state = "SUBMITTED_CONFIRMED"
        draft.official_receipt_id = receipt.id
        proposal.status = str(ProposalStatus.SUBMITTED_CONFIRMED)
        proposal.submitted_at = now
        proposal.submission_receipt = {
            "receipt_id": receipt.id,
            "receipt_number": receipt.receipt_number,
            "is_simulated": True,
            "verified": True,
            "adapter": adapter.name,
            "message": result.message,
            "verification_evidence": result.verification_evidence,
        }
        receipt_payload = proposal.submission_receipt
    else:
        draft.state = "SUBMISSION_FAILED"
        draft.last_error = result.message

    db.add(draft)
    db.add(proposal)
    record_audit(
        db,
        action="correction_submitted",
        session=session,
        household_ref=household.reference,
        member_ref=proposal.member_id,
        entity_type="correction_proposal",
        entity_id=proposal.id,
        outcome="CONFIRMED" if receipt_payload else "FAILED",
        detail={"adapter": adapter.name, "simulated": result.is_simulated, "receipt_present": bool(receipt_payload)},
    )
    db.flush()
    return {
        "proposal": _serialise(proposal, session.member_id or proposal.member_id),
        "accepted": bool(receipt_payload),
        "receipt": receipt_payload,
        "message": result.message,
        "adapter": adapter.name,
        "is_simulated": result.is_simulated,
    }
