"""Portability service: assembles facts and calls the pure rules engine."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.db import ensure_aware, utcnow
from app.domain import Provenance
from app.models import (
    Household,
    Member,
    MemberEntitlement,
    RationShop,
    StockObservation,
    UserSession,
)
from app.rules.loader import load_rule_payload
from app.rules.portability import PortabilityInput, StockFact, evaluate_portability


def _latest_stock(db: DbSession, shop_id: str | None, commodity_code: str) -> StockObservation | None:
    if not shop_id:
        return None
    return db.scalar(
        select(StockObservation)
        .where(StockObservation.shop_id == shop_id, StockObservation.commodity_code == commodity_code)
        .order_by(StockObservation.observed_at.desc())
        .limit(1)
    )


def _latest_entitlement(db: DbSession, member_id: str, commodity_code: str) -> MemberEntitlement | None:
    return db.scalar(
        select(MemberEntitlement)
        .where(MemberEntitlement.member_id == member_id, MemberEntitlement.commodity_code == commodity_code)
        .order_by(MemberEntitlement.period.desc())
        .limit(1)
    )


def evaluate(
    db: DbSession,
    *,
    session: UserSession,
    household: Household,
    member: Member,
    commodity_code: str,
    now: datetime | None = None,
) -> dict[str, Any]:
    now = now or utcnow()
    rules = load_rule_payload(db, "portability")
    stock = _latest_stock(db, household.destination_shop_id, commodity_code)
    entitlement = _latest_entitlement(db, member.id, commodity_code)
    verified_remaining = bool(
        entitlement
        and entitlement.remaining_qty is not None
        and entitlement.provenance in {Provenance.OFFICIAL_VERIFIED, Provenance.OFFICIAL_LAST_SYNCED}
    )
    shop = db.get(RationShop, household.destination_shop_id) if household.destination_shop_id else None

    stock_fact = None
    if stock is not None:
        stock_fact = StockFact(
            state=stock.state,
            observed_at=ensure_aware(stock.observed_at) or now,
            source=stock.source,
            provenance=stock.provenance,
            note=stock.note,
        )

    result = evaluate_portability(
        rules,
        PortabilityInput(
            home_code=household.home_jurisdiction_code,
            destination_code=household.destination_jurisdiction_code,
            commodity_code=commodity_code,
            member_alias=member.display_alias,
            authorization_ok=True,  # member scope already enforced by the endpoint
            identity_evidence_present=bool(household.reference and member.document_ref),
            remaining_verified=verified_remaining,
            remaining_quantity=entitlement.remaining_qty if entitlement else None,
            remaining_unit=entitlement.unit if entitlement else None,
            stock=stock_fact,
            network_online=True,
            now=now,
        ),
    )
    payload = result.to_dict()
    payload["context"] = {
        "household_ref": household.reference,
        "member_id": member.id,
        "member_alias": member.display_alias,
        "home_state": household.home_state,
        "destination_state": household.destination_state,
        "shop": {
            "id": shop.id if shop else None,
            "name": shop.name if shop else "No destination shop configured",
            "address_label": shop.address_label if shop else None,
        },
        "entitlement": {
            "id": entitlement.id if entitlement else None,
            "period": entitlement.period if entitlement else None,
            "provenance": entitlement.provenance if entitlement else None,
            "verification_status": entitlement.verification_status if entitlement else None,
            "remaining_verified": verified_remaining,
        },
        "evaluated_at": now.isoformat(),
        "all_commodities": sorted((rules.get("commodities") or {}).keys()),
    }
    payload["evidence_status"] = [
        {
            "id": "household_reference",
            "label": "Synthetic household reference",
            "present": bool(household.reference),
        },
        {
            "id": "member_identity_reference",
            "label": "Synthetic member identity reference",
            "present": bool(member.document_ref),
        },
        {
            "id": "destination_address_declaration",
            "label": "Destination address declaration (synthetic in demo)",
            "present": False,
            "note": "Not collected in this session. An authorised office may require it.",
        },
    ]
    return payload
