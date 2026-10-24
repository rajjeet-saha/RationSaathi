"""FastAPI security dependencies."""

from __future__ import annotations

from collections.abc import Iterator

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session as DbSession

from app.db import get_db
from app.domain import Permission
from app.models import UserSession
from app.security.sessions import resolve_session


def db_dep() -> Iterator[DbSession]:
    yield from get_db()


def get_current_session(
    x_ration_session: str | None = Header(default=None, alias="X-Ration-Session"),
    authorization: str | None = Header(default=None),
    db: DbSession = Depends(db_dep),
) -> UserSession:
    token = x_ration_session
    if not token and authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "A session is required")
    return resolve_session(db, token)


def require_permission(session: UserSession, permission: Permission) -> None:
    if str(permission) not in (session.permissions or []):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This session does not have permission for that action")


def require_role(*roles: str):
    def _check(session: UserSession = Depends(get_current_session)) -> UserSession:
        if session.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Session role not permitted")
        return session

    return _check
