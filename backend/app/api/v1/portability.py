"""Portability rule source, stock status and stock-state vocabulary."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.db import ensure_aware
from app.domain import PROVENANCE_LABELS, STOCK_STATE_LABELS, StockState
from app.models import RationShop, StockObservation, UserSession
from app.rules.loader import load_rule_payload
from app.security.access import get_household
from app.security.deps import db_dep, get_current_session

router = APIRouter(tags=["portability"])


@router.get("/portability/rules")
def portability_rules(
    session: UserSession = Depends(get_current_session),
    db: DbSession = Depends(db_dep),
) -> dict:
    get_household(db, session)
    rules = load_rule_payload(db, "portability")
    return {
        "rules": rules,
        "is_synthetic": True,
        "notice": "Synthetic demonstration rules. Not a verified statement of current law or policy.",
    }


@router.get("/stock-states")
def stock_states() -> dict:
    return {
        "states": [
            {
                "code": state.value,
                "label": STOCK_STATE_LABELS[state],
                "verified": state
                in {StockState.AVAILABLE_VERIFIED, StockState.OUT_OF_STOCK_VERIFIED},
            }
            for state in StockState
        ],
        "provenance_labels": PROVENANCE_LABELS,
    }


@router.get("/shops/{shop_id}/stock-status")
def stock_status(
    shop_id: str,
    session: UserSession = Depends(get_current_session),
    db: DbSession = Depends(db_dep),
) -> dict:
    household = get_household(db, session)
    shop = db.get(RationShop, shop_id)
    if shop is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Shop record not found")
    if household.destination_shop_id != shop.id:
        # Do not expose arbitrary shops to a household session.
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This shop is outside the household's configured scope")
    observations = db.scalars(
        select(StockObservation)
        .where(StockObservation.shop_id == shop.id)
        .order_by(StockObservation.observed_at.desc())
    ).all()
    latest: dict[str, StockObservation] = {}
    for observation in observations:
        latest.setdefault(observation.commodity_code, observation)
    return {
        "shop": {
            "id": shop.id,
            "name": shop.name,
            "address_label": shop.address_label,
            "is_synthetic": shop.is_synthetic,
        },
        "as_of": ensure_aware(observations[0].observed_at).isoformat() if observations else None,
        "commodities": [
            {
                "commodity_code": code,
                "state": observation.state,
                "state_label": STOCK_STATE_LABELS.get(observation.state, observation.state),
                "observed_at": ensure_aware(observation.observed_at).isoformat(),
                "source": observation.source,
                "provenance": observation.provenance,
                "provenance_label": PROVENANCE_LABELS.get(observation.provenance, observation.provenance),
                "note": observation.note,
            }
            for code, observation in sorted(latest.items())
        ],
        "notice": "Stock information may be stale or incomplete and is not a guarantee of availability.",
    }
