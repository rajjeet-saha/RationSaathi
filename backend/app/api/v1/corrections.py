"""Correction simulation API: block destructive operations server-side."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DbSession

from app.domain import Permission
from app.models import UserSession
from app.schemas import CorrectionDraftRequest, CorrectionSimulateRequest
from app.security.access import get_household
from app.security.deps import db_dep, get_current_session, require_permission
from app.services import correction_service
from app.services.audit import record_audit
from app.services.correction_service import _serialise

router = APIRouter(prefix="/corrections", tags=["corrections"])


@router.post("/simulate")
def simulate(
    body: CorrectionSimulateRequest,
    session: UserSession = Depends(get_current_session),
    db: DbSession = Depends(db_dep),
) -> dict:
    household = get_household(db, session)
    result = correction_service.simulate(db, session=session, household=household, request=body)
    db.commit()
    return result


@router.get("/{proposal_id}")
def get_proposal(
    proposal_id: str,
    session: UserSession = Depends(get_current_session),
    db: DbSession = Depends(db_dep),
) -> dict:
    proposal = correction_service.get_proposal(db, session, proposal_id)
    payload = _serialise(proposal, session.member_id or proposal.member_id)
    payload["evidence_checklist"] = proposal.evidence
    return payload


@router.post("/{proposal_id}/draft")
def save_draft(
    proposal_id: str,
    body: CorrectionDraftRequest,
    session: UserSession = Depends(get_current_session),
    db: DbSession = Depends(db_dep),
) -> dict:
    require_permission(session, Permission.SUBMIT_OFFICIAL_APPLICATION)
    household = get_household(db, session)
    result = correction_service.save_draft(
        db, session=session, household=household, proposal_id=proposal_id, note=body.note
    )
    db.commit()
    return result


@router.post("/{proposal_id}/submit")
def submit(
    proposal_id: str,
    session: UserSession = Depends(get_current_session),
    db: DbSession = Depends(db_dep),
) -> dict:
    require_permission(session, Permission.SUBMIT_OFFICIAL_APPLICATION)
    household = get_household(db, session)
    result = correction_service.submit(db, session=session, household=household, proposal_id=proposal_id)
    db.commit()
    return result
