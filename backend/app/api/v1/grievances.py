"""Grievance, SLA and escalation endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DbSession

from app.domain import Permission
from app.models import UserSession
from app.schemas import EscalationDraftRequest, EscalationSubmitRequest, EscalationUpdateRequest
from app.security.deps import db_dep, get_current_session, require_permission
from app.services import grievance_service

router = APIRouter(prefix="/grievances", tags=["grievances"])


@router.get("")
def list_grievances(
    session: UserSession = Depends(get_current_session),
    db: DbSession = Depends(db_dep),
) -> dict:
    require_permission(session, Permission.VIEW_GRIEVANCE)
    return {
        "grievances": grievance_service.list_grievances(db, session),
        "notice": "Deadlines are only asserted when a configured, verified policy is available.",
    }


@router.get("/{grievance_id}")
def get_grievance(
    grievance_id: str,
    session: UserSession = Depends(get_current_session),
    db: DbSession = Depends(db_dep),
) -> dict:
    require_permission(session, Permission.VIEW_GRIEVANCE)
    return grievance_service.detail(db, session, grievance_id)


@router.post("/{grievance_id}/verify-status")
def verify_status(
    grievance_id: str,
    session: UserSession = Depends(get_current_session),
    db: DbSession = Depends(db_dep),
) -> dict:
    require_permission(session, Permission.VIEW_GRIEVANCE)
    result = grievance_service.refresh_status(db, session, grievance_id)
    db.commit()
    return result


@router.post("/{grievance_id}/escalation-draft")
def escalation_draft(
    grievance_id: str,
    body: EscalationDraftRequest,
    session: UserSession = Depends(get_current_session),
    db: DbSession = Depends(db_dep),
) -> dict:
    require_permission(session, Permission.CREATE_ESCALATION)
    result = grievance_service.create_escalation(
        db,
        session,
        grievance_id,
        recipient_office=body.recipient_office,
        officer_placeholder=body.officer_placeholder,
        safe_contact=body.safe_contact,
        body=body.body,
    )
    db.commit()
    return result


@router.patch("/escalations/{escalation_id}")
def update_escalation(
    escalation_id: str,
    body: EscalationUpdateRequest,
    session: UserSession = Depends(get_current_session),
    db: DbSession = Depends(db_dep),
) -> dict:
    require_permission(session, Permission.CREATE_ESCALATION)
    result = grievance_service.update_escalation(db, session, escalation_id, body.body)
    db.commit()
    return result


@router.post("/escalations/{escalation_id}/submit")
def submit_escalation(
    escalation_id: str,
    body: EscalationSubmitRequest,
    session: UserSession = Depends(get_current_session),
    db: DbSession = Depends(db_dep),
) -> dict:
    require_permission(session, Permission.CREATE_ESCALATION)
    result = grievance_service.submit_escalation(
        db, session, escalation_id, confirm_authorised_channel=body.confirm_authorised_channel
    )
    db.commit()
    return result
