"""Household/member presentation service (member-scoped)."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.db import ensure_aware
from app.domain import PROVENANCE_LABELS, Provenance
from app.models import Commodity, Household, Member, MemberEntitlement, UserSession
from app.security.access import get_household

# Provenance values that may support a derived remaining quantity.
REMAINING_CAPABLE = {Provenance.OFFICIAL_VERIFIED, Provenance.OFFICIAL_LAST_SYNCED}


def remaining_status(entitlement: MemberEntitlement) -> dict[str, Any]:
    """Never invent a remaining quantity from incomplete data."""
    if entitlement.remaining_qty is not None and entitlement.provenance in REMAINING_CAPABLE:
        return {
            "state": "VERIFIED",
            "display": f"{entitlement.remaining_qty:g} {entitlement.unit}",
            "note": "Derived from a synced official record.",
        }
    if entitlement.entitled_qty is not None and entitlement.drawn_qty is not None:
        derived = entitlement.entitled_qty - entitlement.drawn_qty
        return {
            "state": "SYNTHETIC_UNVERIFIED",
            "display": f"{derived:g} {entitlement.unit} (synthetic fixture, not official)",
            "note": "Computed from labelled synthetic values only. Not an official entitlement.",
        }
    return {
        "state": "UNABLE_TO_VERIFY",
        "display": "Unable to verify remaining entitlement",
        "note": "Draw history or provenance is incomplete, so a remaining quantity is not calculated.",
    }


def entitlement_out(entitlement: MemberEntitlement, commodity: Commodity | None = None) -> dict[str, Any]:
    rem = remaining_status(entitlement)
    return {
        "id": entitlement.id,
        "commodity_code": entitlement.commodity_code,
        "commodity_name": commodity.name if commodity else entitlement.commodity_code,
        "commodity_confers_no_legal_entitlement": True,
        "period": entitlement.period,
        "unit": entitlement.unit,
        "entitled_qty": entitlement.entitled_qty,
        "drawn_qty": entitlement.drawn_qty,
        "remaining": rem,
        "provenance": entitlement.provenance,
        "provenance_label": PROVENANCE_LABELS.get(entitlement.provenance, entitlement.provenance),
        "verification_status": entitlement.verification_status,
        "jurisdiction": entitlement.jurisdiction,
        "rules_version": entitlement.rules_version,
        "source_ref": entitlement.source_ref,
        "last_verified_at": ensure_aware(entitlement.last_verified_at).isoformat() if entitlement.last_verified_at else None,
        "is_synthetic": entitlement.provenance == Provenance.SYNTHETIC_DEMO,
    }


def member_out(member: Member, *, include_entitlements: bool = True) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": member.id,
        "household_id": member.household_id,
        "alias": member.display_alias,
        "full_name": member.full_name,
        "age": member.age,
        "age_band": member.age_band,
        "membership_status": member.membership_status,
        "relationship": member.relationship,
        "verification_state": member.verification_state,
        "provenance": member.provenance,
        "provenance_label": PROVENANCE_LABELS.get(member.provenance, member.provenance),
        "consent_state": member.consent_state,
        "is_head": member.is_head,
        "is_absent": member.is_absent,
        "is_dependent": member.is_dependent,
        "document": {
            "name": member.document_name,
            "age": member.document_age,
            "ref": member.document_ref,
            "provenance": member.document_provenance,
            "provenance_label": PROVENANCE_LABELS.get(member.document_provenance or "", "Source unknown"),
        },
        "last_verified_at": ensure_aware(member.last_verified_at).isoformat() if member.last_verified_at else None,
        "privacy_notice": "This profile is scoped to the current session. Other members' records are not included.",
    }
    if include_entitlements:
        data["entitlements"] = [entitlement_out(e) for e in member.entitlements]
    return data


def household_out(db: DbSession, session: UserSession) -> dict[str, Any]:
    household = get_household(db, session)
    member = db.get(Member, session.member_id) if session.member_id else None
    if member is None:
        raise ValueError("Session has no member scope")
    member_count = len(household.members)
    own_entitlements = [entitlement_out(e) for e in member.entitlements]
    return {
        "id": household.id,
        "reference": household.reference,
        "label": household.label,
        "home_state": household.home_state,
        "home_jurisdiction_code": household.home_jurisdiction_code,
        "destination_state": household.destination_state,
        "destination_jurisdiction_code": household.destination_jurisdiction_code,
        "destination_shop_id": household.destination_shop_id,
        "provenance": household.provenance,
        "provenance_label": PROVENANCE_LABELS.get(household.provenance, household.provenance),
        "last_verified_at": ensure_aware(household.last_verified_at).isoformat() if household.last_verified_at else None,
        "last_synced_at": ensure_aware(household.last_synced_at).isoformat() if household.last_synced_at else None,
        "member_count": member_count,
        "is_synthetic": household.is_synthetic,
        "session": {
            "role": session.role,
            "member_id": session.member_id,
            "expires_at": ensure_aware(session.expires_at).isoformat(),
            "permissions": session.permissions,
            "consent_members": session.consent_member_ids,
        },
        "current_member": member_out(member),
        "own_entitlements": own_entitlements,
        "notice": (
            "Household membership count only. Other members' identity and entitlement details are hidden in this session."
        ),
    }


def commodities_map(db: DbSession) -> dict[str, Commodity]:
    return {c.code: c for c in db.scalars(select(Commodity)).all()}
