"""Offline and assisted-service draft endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DbSession

from app.models import UserSession
from app.schemas import DraftCreateRequest, DraftSyncRequest, DraftUpdateRequest, DraftVerifyRequest
from app.security.deps import db_dep, get_current_session
from app.services import draft_service

router = APIRouter(prefix="/drafts", tags=["drafts"])


@router.get("")
def list_drafts(
    session: UserSession = Depends(get_current_session),
    db: DbSession = Depends(db_dep),
) -> dict:
    drafts = draft_service.list_drafts(db, session)
    return {
        "drafts": drafts,
        "states": [
            "DRAFT_NOT_SUBMITTED",
            "QUEUED_FOR_SYNC",
            "SYNC_IN_PROGRESS",
            "SUBMISSION_PENDING_VERIFICATION",
            "SUBMITTED_CONFIRMED",
            "SUBMISSION_FAILED",
            "REQUIRES_REVIEW",
            "CANCELLED",
        ],
        "notice": "A local draft reference is never an official receipt. Only a verified adapter acknowledgement is shown as confirmed.",
    }


@router.post("", status_code=201)
def create_draft(
    body: DraftCreateRequest,
    session: UserSession = Depends(get_current_session),
    db: DbSession = Depends(db_dep),
) -> dict:
    result = draft_service.create_draft(db, session, body.model_dump())
    db.commit()
    return result


@router.patch("/{draft_id}")
def update_draft(
    draft_id: str,
    body: DraftUpdateRequest,
    session: UserSession = Depends(get_current_session),
    db: DbSession = Depends(db_dep),
) -> dict:
    result = draft_service.update_draft(db, session, draft_id, body.payload, body.expected_version)
    db.commit()
    return result


@router.post("/{draft_id}/sync")
def sync_draft(
    draft_id: str,
    body: DraftSyncRequest,
    session: UserSession = Depends(get_current_session),
    db: DbSession = Depends(db_dep),
) -> dict:
    result = draft_service.sync_draft(db, session, draft_id, body.network_online)
    db.commit()
    return result


@router.post("/{draft_id}/verify-submission")
def verify_submission(
    draft_id: str,
    body: DraftVerifyRequest,
    session: UserSession = Depends(get_current_session),
    db: DbSession = Depends(db_dep),
) -> dict:
    result = draft_service.verify_submission(db, session, draft_id, body.simulate_receipt)
    db.commit()
    return result


@router.delete("/{draft_id}")
def delete_draft(
    draft_id: str,
    session: UserSession = Depends(get_current_session),
    db: DbSession = Depends(db_dep),
) -> dict:
    result = draft_service.cancel_draft(db, session, draft_id)
    db.commit()
    return result
