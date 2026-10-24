"""Demo-mode endpoints: synthetic sign-in directory, scenario facts and reset."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session as DbSession

from app.config import get_settings
from app.db import ensure_aware
from app.models import Grievance, Household, Member, OfflineDraft, StockObservation, UserSession
from app.security.deps import db_dep

router = APIRouter(prefix="/demo", tags=["demo"])


def _require_demo() -> None:
    if not get_settings().demo_mode:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Demo mode is disabled")


@router.get("/status")
def demo_status() -> dict:
    settings = get_settings()
    return {
        "demo_mode": settings.demo_mode,
        "simulated_submission": settings.allow_simulated_submission,
        "rules_version": settings.rules_version,
        "notice": (
            "RationSaathi demo. All households, members, stock records, receipts and grievances are synthetic. "
            "No government system is connected."
        ),
        "limitations": [
            "Identity selection is a simulated demo sign-in, not production authentication.",
            "Submissions go to a labelled simulator; receipts are not government receipts.",
            "Deadlines use synthetic configured policies, not legal service standards.",
        ],
    }


@router.get("/profiles")
def demo_profiles(db: DbSession = Depends(db_dep)) -> dict:
    """Synthetic profile directory used only by the demo sign-in selector."""
    _require_demo()
    households = db.scalars(select(Household).order_by(Household.reference)).all()
    payload = []
    for household in households:
        members = db.scalars(
            select(Member).where(Member.household_id == household.id).order_by(Member.is_head.desc())
        ).all()
        payload.append(
            {
                "id": household.id,
                "reference": household.reference,
                "label": household.label,
                "home_state": household.home_state,
                "destination_state": household.destination_state,
                "is_synthetic": household.is_synthetic,
                "members": [
                    {
                        "id": member.id,
                        "alias": member.display_alias,
                        "relationship": member.relationship,
                        "age_band": member.age_band or ("adult" if (member.age or 0) >= 18 else "child"),
                        "is_head": member.is_head,
                        "is_absent": member.is_absent,
                        "is_dependent": member.is_dependent,
                        "verification_state": member.verification_state,
                    }
                    for member in members
                ],
            }
        )
    return {
        "households": payload,
        "notice": (
            "SIMULATED DEMO SIGN-IN DIRECTORY. Real deployments must use an authorised identity provider; "
            "this endpoint is disabled outside demo mode."
        ),
    }


@router.get("/scenario")
def demo_scenario(db: DbSession = Depends(db_dep)) -> dict:
    _require_demo()
    households = db.scalars(select(Household)).all()
    members = db.scalars(select(Member)).all()
    drafts = db.scalars(select(OfflineDraft)).all()
    grievances = db.scalars(select(Grievance)).all()
    stocks = db.scalars(select(StockObservation)).all()
    sessions = db.scalar(select(func.count()).select_from(UserSession).where(UserSession.ended_at.is_(None))) or 0
    oldest_grievance = min(
        (ensure_aware(g.filed_at) for g in grievances if g.filed_at),
        default=None,
    )
    return {
        "is_synthetic": True,
        "households": len(households),
        "members": len(members),
        "household_a_members": sum(1 for m in members if m.household_id == "hh-syn-1042"),
        "unsubmitted_drafts": [d.draft_ref for d in drafts if d.state == "DRAFT_NOT_SUBMITTED"],
        "grievances": [
            {
                "id": g.id,
                "filed_at": ensure_aware(g.filed_at).isoformat() if g.filed_at else None,
                "deadline_verified": g.deadline_verified,
                "status": g.status,
                "category": g.category,
            }
            for g in grievances
        ],
        "stock_states": sorted({s.state for s in stocks}),
        "active_sessions": sessions,
        "oldest_grievance_filed_at": oldest_grievance.isoformat() if oldest_grievance else None,
        "checks": [
            "five synthetic household members seeded",
            "member-level entitlements with provenance",
            "reported out-of-stock commodity",
            "stale stock observation",
            "draft marked DRAFT — NOT SUBMITTED",
            "grievance filed 21 days ago with unverified deadline",
            "separate household for handover isolation",
        ],
    }


@router.post("/reset")
def demo_reset(db: DbSession = Depends(db_dep)) -> dict:
    _require_demo()
    from scripts.seed import reset_and_seed

    db.close()
    summary = reset_and_seed()
    return {
        "reset": True,
        "summary": summary,
        "notice": "All sessions were invalidated and synthetic fixtures were recreated deterministically.",
    }
