"""Session and access endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.config import get_settings
from app.db import ensure_aware
from app.domain import Permission, Provenance
from app.models import Household, Member, UserSession
from app.schemas import ConfirmConsentRequest, SessionCreateRequest, SessionEndRequest, SessionSwitchRequest
from app.security.access import (
    action_policy,
    get_household,
    grant_facilitator_consent,
    load_authorisation_policy,
    require_member_access,
)
from app.security.deps import db_dep, get_current_session, require_permission
from app.security.sessions import create_session, end_session
from app.services.audit import record_audit
from app.services.households import member_out

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _session_payload(session: UserSession, member: Member | None, household: Household) -> dict:
    return {
        "role": session.role,
        "session_id": session.id,
        "household": {
            "id": household.id,
            "reference": household.reference,
            "label": household.label,
            "home_state": household.home_state,
            "destination_state": household.destination_state,
        },
        "member": member_out(member) if member else None,
        "permissions": session.permissions,
        "consent_member_ids": session.consent_member_ids,
        "purpose": session.purpose,
        "expires_at": ensure_aware(session.expires_at).isoformat(),
        "demo_notice": "SIMULATED DEMO SIGN-IN. This selector is not production authentication.",
        "policy_version": load_authorisation_policy().get("version"),
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def start_session(
    body: SessionCreateRequest,
    db: DbSession = Depends(db_dep),
) -> dict:
    settings = get_settings()
    if not settings.demo_mode:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Demo identity selection is disabled. Configure an authorised authentication integration.",
        )
    household = db.get(Household, body.household_id)
    if household is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Household not found")
    member = db.get(Member, body.member_id) if body.member_id else None
    if body.role == "MEMBER" and member is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Select a member profile")
    if body.role == "FACILITATOR" and body.member_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "A facilitator session must capture consent before opening a profile")

    session, token = create_session(
        db,
        household=household,
        role=body.role,
        member=member,
        purpose=body.purpose,
        facilitator_device=body.facilitator_device or "shared-demo-device-01",
    )
    record_audit(
        db,
        action="session_started",
        session=session,
        household_ref=household.reference,
        member_ref=session.member_id,
        entity_type="session",
        entity_id=session.id,
        detail={"role": session.role, "purpose": session.purpose},
    )
    db.commit()
    return {"token": token, **_session_payload(session, member, household)}


@router.get("/current")
def current_session(
    session: UserSession = Depends(get_current_session),
    db: DbSession = Depends(db_dep),
) -> dict:
    household = get_household(db, session)
    member = db.get(Member, session.member_id) if session.member_id else None
    return _session_payload(session, member, household)


@router.get("/me/permissions")
def my_permissions(
    session: UserSession = Depends(get_current_session),
    db: DbSession = Depends(db_dep),
) -> dict:
    household = get_household(db, session)
    return {
        "role": session.role,
        "permissions": session.permissions,
        "member_id": session.member_id,
        "household_reference": household.reference,
        "policy": load_authorisation_policy(),
        "actions": {
            "view_own_profile": action_policy("view_own_profile"),
            "view_other_member": action_policy("view_other_member"),
            "change_membership": action_policy("change_membership"),
            "give_consent_for_other": action_policy("give_consent_for_other"),
        },
        "note": "Authorisation is enforced server-side. These values describe the current session only.",
    }


@router.post("/consent")
def facilitator_consent(
    body: ConfirmConsentRequest,
    session: UserSession = Depends(get_current_session),
    db: DbSession = Depends(db_dep),
) -> dict:
    household = get_household(db, session)
    member = db.get(Member, body.member_id)
    if member is None or member.household_id != household.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Member record not found")
    consent = grant_facilitator_consent(
        db,
        session,
        member,
        consent_explained=body.consent_explained,
        consent_given=body.consent_given,
    )
    record_audit(
        db,
        action="facilitator_consent_recorded",
        session=session,
        household_ref=household.reference,
        member_ref=member.id,
        entity_type="member_consent",
        entity_id=consent.id,
        detail={"scope": consent.scope},
    )
    db.commit()
    return {
        "consent_id": consent.id,
        "member_id": member.id,
        "scope": consent.scope,
        "recorded_at": ensure_aware(consent.recorded_at).isoformat(),
        "scope_notice": "Consent applies to this session only and is revoked when the session ends.",
        "member": member_out(member),
    }


@router.post("/switch")
def switch_profile(
    body: SessionSwitchRequest,
    session: UserSession = Depends(get_current_session),
    db: DbSession = Depends(db_dep),
) -> dict:
    """Demo-only profile switch: ends the old session and issues a new scoped one."""
    settings = get_settings()
    if not settings.demo_mode:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Profile switching requires re-authentication")
    household = get_household(db, session)
    member = db.get(Member, body.member_id)
    if member is None or member.household_id != household.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Member record not found")
    if session.role == "FACILITATOR":
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "End the assisted session and start a new one with fresh consent before opening another member's profile.",
        )
    ended = end_session(db, session, "PROFILE_SWITCH", client_cleanup_confirmed=False)
    new_session, token = create_session(
        db,
        household=household,
        role="MEMBER",
        member=member,
        purpose="MEMBER_SELF_SERVICE",
    )
    record_audit(
        db,
        action="profile_switched_demo",
        session=new_session,
        household_ref=household.reference,
        member_ref=member.id,
        entity_type="session",
        entity_id=new_session.id,
        detail={"previous_session_revoked": True},
    )
    db.commit()
    return {
        "token": token,
        "previous_session": ended,
        **_session_payload(new_session, member, household),
        "cleanup_notice": "The previous session token is revoked, but the browser must also clear its in-memory state.",
    }


@router.post("/end")
def terminate_session(
    body: SessionEndRequest,
    session: UserSession = Depends(get_current_session),
    db: DbSession = Depends(db_dep),
) -> dict:
    household = get_household(db, session)
    result = end_session(db, session, body.reason, body.client_cleanup_confirmed)
    record_audit(
        db,
        action="session_ended",
        session=session,
        household_ref=household.reference,
        entity_type="session",
        entity_id=session.id,
        detail={
            "reason": body.reason,
            "client_cleanup_confirmed": body.client_cleanup_confirmed,
            "server_cleanup": True,
        },
    )
    db.commit()
    return {
        **result,
        "household_reference": household.reference,
        "notice": "Session closed. The token cannot be reused. Device-level artifacts outside the app may persist.",
    }
