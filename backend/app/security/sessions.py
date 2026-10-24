"""Session creation, validation and termination.

Tokens are random opaque values returned once; only a SHA-256 hash is stored.
Sessions are row-backed so logout/cleanup can be verified server side. A member
profile switch revokes the old token and issues a new, unrelated one.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session as DbSession

from app.config import get_settings
from app.db import ensure_aware, utcnow
from app.domain import ROLE_PERMISSIONS, SessionRole
from app.models import Household, Member, UserSession


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _issue_token(db: DbSession, session: UserSession) -> str:
    token = secrets.token_urlsafe(32)
    session.token_hash = hash_token(token)
    db.add(session)
    return token


def create_session(
    db: DbSession,
    *,
    household: Household,
    role: str,
    member: Member | None,
    purpose: str,
    facilitator_device: str | None = None,
) -> tuple[UserSession, str]:
    settings = get_settings()
    if role not in set(SessionRole):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unsupported role")
    if role == SessionRole.MEMBER and member is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "A member session must select a member profile")
    if member is not None and member.household_id != household.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Member does not belong to this household")
    if role == SessionRole.PUBLIC:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Public users do not create identified sessions")

    active = db.scalar(
        select(func.count())
        .select_from(UserSession)
        .where(UserSession.household_id == household.id, UserSession.ended_at.is_(None))
    )
    if active and active >= settings.max_active_sessions_per_household:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many active sessions for this household")

    ttl = settings.facilitator_session_ttl_minutes if role == SessionRole.FACILITATOR else settings.session_ttl_minutes
    session = UserSession(
        role=role,
        household_id=household.id,
        member_id=member.id if member else None,
        permissions=list(ROLE_PERMISSIONS.get(role, ())),
        consent_member_ids=[],
        facilitator_device=facilitator_device,
        purpose=purpose,
        expires_at=utcnow() + timedelta(minutes=ttl),
    )
    token = _issue_token(db, session)
    db.flush()
    return session, token


def end_session(db: DbSession, session: UserSession, reason: str, client_cleanup_confirmed: bool = False) -> dict:
    if session.ended_at is None:
        session.ended_at = utcnow()
        session.ended_reason = reason
        if client_cleanup_confirmed:
            session.cleanup_verified_at = utcnow()
        session.token_hash = f"revoked:{session.id}:{secrets.token_hex(8)}"
        db.add(session)
    db.flush()
    return {
        "session_id": session.id,
        "ended": True,
        "ended_reason": session.ended_reason,
        "server_cleanup_verified": session.cleanup_verified_at is not None,
        "server_actions": [
            "session token revoked",
            "session scope closed",
            "member consent grants for this session are no longer usable",
        ],
        "client_actions_required": [
            "private React state cleared",
            "session keys revoked in memory",
            "cached drafts and object URLs removed",
            "back-navigation guard remains active",
        ],
        "limitations": [
            "A web app cannot delete operating-system backups, screenshots or external copies.",
            "Browser-managed caches outside this app's control may persist until cleared by the device.",
        ],
    }


def resolve_session(db: DbSession, token: str) -> UserSession:
    token_hash = hash_token(token)
    session = db.scalar(select(UserSession).where(UserSession.token_hash == token_hash))
    if session is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired session")
    if session.ended_at is not None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session has ended")
    if ensure_aware(session.expires_at) <= utcnow():
        session.ended_at = utcnow()
        session.ended_reason = "TIMEOUT"
        db.add(session)
        db.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session has expired")
    return session
