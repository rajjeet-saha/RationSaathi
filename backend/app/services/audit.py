"""Append-only audit logging without sensitive values."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session as DbSession

from app.models import AuditEvent, UserSession


def record_audit(
    db: DbSession,
    *,
    action: str,
    session: UserSession | None = None,
    household_ref: str | None = None,
    member_ref: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    outcome: str = "OK",
    detail: dict[str, Any] | None = None,
) -> AuditEvent:
    event = AuditEvent(
        action=action,
        actor_role=session.role if session else None,
        session_ref=session.id[:8] if session else None,
        household_ref=household_ref,
        member_ref=member_ref,
        entity_type=entity_type,
        entity_id=entity_id,
        outcome=outcome,
        detail=detail or {},
    )
    db.add(event)
    return event
