"""Public, de-identified aggregate endpoints (no session required)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session as DbSession

from app.security.deps import db_dep
from app.security.ratelimit import rate_limit
from app.services.aggregates import public_aggregates

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/aggregates")
def aggregates(request: Request, db: DbSession = Depends(db_dep)) -> dict:
    rate_limit(request, key="public-aggregates", limit=60, window_seconds=60)
    return public_aggregates(db)
