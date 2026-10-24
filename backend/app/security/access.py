"""Server-side authorisation for member-scoped operations.

Every protected operation checks the authenticated session, its household scope,
the required permission and member consent. The frontend is never trusted to
enforce this.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session as DbSession

from app.domain import Permission, SessionRole
from app.models import Household, Member, MemberConsent, UserSession

POLICY_PATH = Path(__file__).resolve().parent.parent / "rules" / "authorisation_policy.json"


@lru_cache
def load_authorisation_policy() -> dict[str, Any]:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def action_policy(action: str) -> dict[str, Any]:
    return load_authorisation_policy().get("actions", {}).get(action, {"requires": ["unknown_action"], "resolved": False})


def get_household(db: DbSession, session: UserSession) -> Household:
    if session.household_id is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This session is not scoped to a household")
    household = db.get(Household, session.household_id)
    if household is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Household record not found")
    return household


def get_member(db: DbSession, member_id: str) -> Member:
    member = db.get(Member, member_id)
    if member is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Member record not found")
    return member


def can_view_member(session: UserSession, member: Member) -> bool:
    if member.household_id != session.household_id:
        return False
    if session.role == SessionRole.MEMBER:
        return session.member_id == member.id
    if session.role == SessionRole.FACILITATOR:
        return session.member_id == member.id and member.id in (session.consent_member_ids or [])
    return False


def require_member_access(session: UserSession, member: Member) -> None:
    if not can_view_member(session, member):
        # Deliberately do not reveal whether the other member exists.
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This profile is outside the current session's authorised scope")


def authorise_member_read(db: DbSession, session: UserSession, member_id: str) -> Member:
    member = get_member(db, member_id)
    require_member_access(session, member)
    return member


def grant_facilitator_consent(
    db: DbSession,
    session: UserSession,
    member: Member,
    *,
    consent_explained: bool,
    consent_given: bool,
) -> MemberConsent:
    if session.role != SessionRole.FACILITATOR:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only a facilitator session records assisted consent")
    if member.household_id != session.household_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Member is outside this assisted session")
    if not consent_explained or not consent_given:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Record the explanation and the member's consent before opening a profile")
    if session.member_id and session.member_id != member.id:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "This assisted session is already scoped to another member. End the session and start a new one.",
        )
    session.member_id = member.id
    grants = list(session.consent_member_ids or [])
    if member.id not in grants:
        grants.append(member.id)
    session.consent_member_ids = grants
    consent = MemberConsent(
        member_id=member.id,
        scope="facilitator_view_and_draft_preparation",
        granted=True,
        provenance="FACILITATOR_ENTERED",
        recorded_by_session=session.id,
    )
    db.add(session)
    db.add(consent)
    db.flush()
    return consent


def actor_capabilities(session: UserSession) -> dict[str, bool]:
    """What this session may do, independent of the requested target member."""
    is_member = session.role == SessionRole.MEMBER
    return {
        "can_change_identity": is_member and Permission.CHANGE_IDENTITY_FIELDS in (session.permissions or []),
        "can_change_membership": is_member and Permission.CHANGE_MEMBERSHIP in (session.permissions or []),
        "can_submit": Permission.SUBMIT_OFFICIAL_APPLICATION in (session.permissions or []),
        "is_facilitator": session.role == SessionRole.FACILITATOR,
    }


def require_self_or_authorised(session: UserSession, member_id: str) -> None:
    """Identity edits are self-service in this prototype; guardianship needs review."""
    if session.role != SessionRole.MEMBER or session.member_id != member_id:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Changes to another adult's identity fields are not permitted. Use an authorised review process.",
        )
