"""Member-scoped household endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DbSession

from app.domain import Permission
from app.models import UserSession
from app.schemas import PortabilityEvaluateRequest
from app.security.access import get_household, require_member_access
from app.security.deps import db_dep, get_current_session, require_permission
from app.services import portability_service
from app.services.households import entitlement_out, household_out, member_out

router = APIRouter(tags=["household"])


@router.get("/households/current")
def current_household(
    session: UserSession = Depends(get_current_session),
    db: DbSession = Depends(db_dep),
) -> dict:
    require_permission(session, Permission.VIEW_OWN_PROFILE)
    if session.member_id is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Record member consent before opening a household profile in an assisted session",
        )
    return household_out(db, session)


@router.get("/members/{member_id}")
def get_member(
    member_id: str,
    session: UserSession = Depends(get_current_session),
    db: DbSession = Depends(db_dep),
) -> dict:
    from app.models import Member

    member = db.get(Member, member_id)
    if member is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Member record not found")
    require_member_access(session, member)
    return member_out(member)


@router.get("/members/{member_id}/entitlements")
def get_member_entitlements(
    member_id: str,
    session: UserSession = Depends(get_current_session),
    db: DbSession = Depends(db_dep),
) -> dict:
    from app.models import Member

    member = db.get(Member, member_id)
    if member is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Member record not found")
    require_member_access(session, member)
    return {
        "member_id": member.id,
        "member_alias": member.display_alias,
        "entitlements": [entitlement_out(e) for e in member.entitlements],
        "notice": (
            "Quantities are labelled synthetic fixtures unless provenance is marked official. "
            "A household-reported value is never upgraded automatically."
        ),
    }


@router.post("/portability/evaluate")
def evaluate(
    body: PortabilityEvaluateRequest,
    session: UserSession = Depends(get_current_session),
    db: DbSession = Depends(db_dep),
) -> dict:
    from app.models import Member

    member = db.get(Member, body.member_id)
    if member is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Member record not found")
    require_member_access(session, member)
    household = get_household(db, session)
    return portability_service.evaluate(
        db,
        session=session,
        household=household,
        member=member,
        commodity_code=body.commodity_code,
    )
