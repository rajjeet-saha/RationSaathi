"""Deterministic, versioned portability rules engine.

Pure functions: no database or FastAPI imports. The caller supplies the active
synthetic rule record and a snapshot of household/stock facts. Tests exercise
this module directly.

The engine never asserts a legal entitlement, statutory deadline or live stock
availability. Every answer carries the rule version, provenance and uncertainty.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from app.domain import STOCK_STATE_LABELS, Decision, StockState


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


@dataclass(frozen=True)
class StockFact:
    state: str
    observed_at: datetime
    source: str
    provenance: str
    note: str | None = None


@dataclass(frozen=True)
class PortabilityInput:
    home_code: str
    destination_code: str
    commodity_code: str
    member_alias: str | None
    authorization_ok: bool
    identity_evidence_present: bool
    remaining_verified: bool
    remaining_quantity: float | None
    remaining_unit: str | None
    stock: StockFact | None
    network_online: bool
    now: datetime


@dataclass
class PortabilityResult:
    decision: str
    eligible_to_proceed: bool
    travel_recommended: bool
    headline: str
    reasons: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    required_evidence: list[str] = field(default_factory=list)
    authority_to_contact: list[str] = field(default_factory=list)
    alternative_pathways: list[dict[str, str]] = field(default_factory=list)
    cannot_guarantee: list[str] = field(default_factory=list)
    stock: dict[str, Any] | None = None
    rule: dict[str, Any] = field(default_factory=dict)
    commodity: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "eligible_to_proceed": self.eligible_to_proceed,
            "travel_recommended": self.travel_recommended,
            "headline": self.headline,
            "reasons": self.reasons,
            "assumptions": self.assumptions,
            "required_evidence": self.required_evidence,
            "authority_to_contact": self.authority_to_contact,
            "alternative_pathways": self.alternative_pathways,
            "cannot_guarantee": self.cannot_guarantee,
            "stock": self.stock,
            "rule": self.rule,
            "commodity": self.commodity,
        }


def _find_pair(rules: dict[str, Any], home: str, destination: str) -> dict[str, Any] | None:
    for pair in rules.get("pairs", []):
        if pair.get("home") == home and pair.get("destination") == destination:
            return pair
    return None


def evaluate_portability(rules: dict[str, Any], data: PortabilityInput) -> PortabilityResult:
    now = _aware(data.now)
    rule_meta = {
        "version": rules.get("version", "unknown"),
        "source_label": rules.get("source_label", "Unknown rule source"),
        "is_synthetic": bool(rules.get("is_synthetic", True)),
        "effective_from": rules.get("effective_from"),
        "disclaimers": rules.get("disclaimers", []),
    }
    commodity_meta = dict(rules.get("commodities", {}).get(data.commodity_code, {}))
    commodity_meta.setdefault("code", data.commodity_code)

    pair = _find_pair(rules, data.home_code, data.destination_code)
    if pair is None:
        return PortabilityResult(
            decision=Decision.CANNOT_DETERMINE,
            eligible_to_proceed=False,
            travel_recommended=False,
            headline="No configured portability rule covers this state pair.",
            reasons=[
                "The configured synthetic rules do not include this home-state / destination-state pair.",
                "This is not a statement that portability is legally unavailable.",
            ],
            required_evidence=list(rules.get("identity_evidence_options", [])),
            authority_to_contact=["Home-state ration office", "Destination-shop authorised office"],
            cannot_guarantee=["No rule exists, so no outcome can be predicted safely."],
            rule=rule_meta,
            commodity=commodity_meta,
        )

    if not pair.get("portability_supported"):
        return PortabilityResult(
            decision=Decision.NOT_SUPPORTED,
            eligible_to_proceed=False,
            travel_recommended=False,
            headline="The configured rules do not describe a portability pathway for this pair.",
            reasons=["Synthetic rule explicitly marks this pair as unsupported."],
            authority_to_contact=["Home-state ration office"],
            cannot_guarantee=["Absence of a configured pathway is not proof that no lawful option exists."],
            rule=rule_meta,
            commodity=commodity_meta,
        )

    if data.commodity_code not in pair.get("commodities", []):
        return PortabilityResult(
            decision=Decision.NOT_SUPPORTED,
            eligible_to_proceed=False,
            travel_recommended=False,
            headline=f"{commodity_meta.get('name', data.commodity_code)} is not covered by the configured rule for this pair.",
            reasons=["The synthetic rule lists only: " + ", ".join(pair.get("commodities", []))],
            authority_to_contact=["Destination-shop authorised office"],
            cannot_guarantee=["The commodity may still be available through another lawful process not modelled here."],
            rule=rule_meta,
            commodity=commodity_meta,
        )

    required_evidence = list(pair.get("required_evidence", []))
    authority = ["Destination-shop authorised office"]
    if pair.get("requires_home_state_confirmation"):
        authority.insert(0, "Home-state ration office")

    if not data.network_online:
        authority.append("Facilitator assistance centre (offline guidance only)")

    notes: list[str] = list(pair.get("notes", []))
    assumptions = [
        "The household reference and member reference are synthetic test values.",
        "Entitlement quantities come from labelled synthetic fixtures.",
    ]

    stock = data.stock
    stock_detail: dict[str, Any] | None = None
    freshness = timedelta(hours=int(rules.get("stock_freshness_hours", 24)))
    effective_state = StockState.UNKNOWN
    if stock is None:
        effective_state = StockState.SOURCE_UNAVAILABLE
        stock_detail = {
            "state": effective_state,
            "label": STOCK_STATE_LABELS[effective_state],
            "observed_at": None,
            "source": "No stock source configured",
            "provenance": "UNKNOWN",
            "age_hours": None,
            "freshness_hours": freshness.total_seconds() / 3600,
            "note": "No stock observation is recorded for this shop and commodity.",
        }
    else:
        observed = _aware(stock.observed_at)
        age = now - observed
        state = stock.state
        if state not in set(StockState):
            state = StockState.UNKNOWN
        if state in {StockState.AVAILABLE_VERIFIED, StockState.REPORTED_AVAILABLE, StockState.OUT_OF_STOCK_VERIFIED, StockState.OUT_OF_STOCK_REPORTED} and age > freshness:
            state = StockState.STALE
        effective_state = StockState(state)
        stock_detail = {
            "state": effective_state,
            "label": STOCK_STATE_LABELS[effective_state],
            "observed_at": observed.isoformat(),
            "age_hours": round(max(age.total_seconds(), 0) / 3600, 1),
            "freshness_hours": freshness.total_seconds() / 3600,
            "source": stock.source,
            "provenance": stock.provenance,
            "note": stock.note,
        }

    # Alternative pathways: conservative, never a promise.
    alternatives: list[dict[str, str]] = [
        {
            "id": "confirm_with_shop",
            "title": "Ask the authorised shop to confirm today's stock",
            "detail": "Stock reports can be incomplete. The shop is the only place that can confirm availability for today.",
            "certainty": "UNVERIFIED",
        }
    ]
    if pair.get("alternate_shop_allowed"):
        alternatives.append(
            {
                "id": "alternate_shop",
                "title": "Ask the responsible office about an authorised alternative shop",
                "detail": "The synthetic rule allows an alternative-shop pathway, but availability and eligibility at another shop are not verified.",
                "certainty": "UNVERIFIED",
            }
        )
    window = rules.get("collection_windows", {}).get(data.destination_code)
    if window:
        alternatives.append(
            {
                "id": "later_window",
                "title": "Ask about a later collection window",
                "detail": f"{window.get('label')}. This schedule is illustrative and unverified; a return visit may be needed.",
                "certainty": "UNVERIFIED",
            }
        )
    alternatives.append(
        {
            "id": "facilitator_help",
            "title": "Ask a facilitator or the responsible office for help",
            "detail": "An assisted-service centre can help confirm evidence requirements without sharing more data than necessary.",
            "certainty": "UNVERIFIED",
        }
    )

    base_kwargs = {
        "required_evidence": required_evidence,
        "assumptions": assumptions,
        "authority_to_contact": authority,
        "alternative_pathways": alternatives,
        "stock": stock_detail,
        "rule": rule_meta,
        "commodity": commodity_meta,
    }

    if not data.authorization_ok:
        return PortabilityResult(
            decision=Decision.MORE_INFORMATION,
            eligible_to_proceed=False,
            travel_recommended=False,
            headline="Authority for this request has not been established.",
            reasons=[
                "This session is not authorised to request a portability service for this member.",
                "The absent household head is not assumed to have authorised this action.",
            ],
            cannot_guarantee=["Without verified authority the outcome cannot be predicted."],
            **base_kwargs,
        )

    if not data.identity_evidence_present:
        return PortabilityResult(
            decision=Decision.MORE_INFORMATION,
            eligible_to_proceed=False,
            travel_recommended=False,
            headline="Identity evidence is incomplete for the configured pathway.",
            reasons=["A required household or member reference is missing or unverified.", *notes],
            cannot_guarantee=["A missing record in this demo does not prove ineligibility."],
            **base_kwargs,
        )

    if effective_state in {StockState.OUT_OF_STOCK_REPORTED, StockState.OUT_OF_STOCK_VERIFIED}:
        verified = effective_state == StockState.OUT_OF_STOCK_VERIFIED
        return PortabilityResult(
            decision=Decision.MORE_INFORMATION,
            eligible_to_proceed=False,
            travel_recommended=False,
            headline=(
                f"{commodity_meta.get('name', data.commodity_code)} is reported unavailable at this shop."
                if not verified
                else f"{commodity_meta.get('name', data.commodity_code)} is verified unavailable at this shop."
            ),
            reasons=[
                "Stock information can change and may be incomplete.",
                "No alternative availability, substitution or reimbursement is promised.",
                *notes,
            ],
            cannot_guarantee=[
                "A stock report is not a guarantee about any other shop or a future visit.",
                "No commodity substitution or extra quantity is represented by these rules.",
            ],
            **base_kwargs,
        )

    if effective_state in {StockState.STALE, StockState.UNKNOWN, StockState.SOURCE_UNAVAILABLE}:
        headline = {
            StockState.STALE: "Stock information is stale and cannot be confirmed.",
            StockState.SOURCE_UNAVAILABLE: "No stock source is available, so availability cannot be confirmed.",
        }.get(effective_state, "Stock is unknown and cannot be confirmed from the available information.")
        return PortabilityResult(
            decision=Decision.CANNOT_DETERMINE,
            eligible_to_proceed=False,
            travel_recommended=False,
            headline=headline,
            reasons=[
                "The last stock observation is stale, missing or unavailable.",
                "Do not travel based on unverified stock information.",
                *notes,
            ],
            cannot_guarantee=["Today's availability at the shop is unknown."],
            **base_kwargs,
        )

    if effective_state == StockState.REPORTED_AVAILABLE:
        return PortabilityResult(
            decision=Decision.POTENTIALLY_ELIGIBLE,
            eligible_to_proceed=False,
            travel_recommended=False,
            headline="Stock is reported available but not verified, and your entitlement record needs confirmation.",
            reasons=[
                "A household-reported stock state is weaker evidence than a verified shop record.",
                "Confirm your remaining quantity with the authorised shop before relying on it.",
                *notes,
            ],
            cannot_guarantee=["Reported availability may be outdated or inaccurate."],
            **base_kwargs,
        )

    # AVAILABLE_VERIFIED
    if not data.remaining_verified or data.remaining_quantity is None:
        return PortabilityResult(
            decision=Decision.POTENTIALLY_ELIGIBLE,
            eligible_to_proceed=False,
            travel_recommended=False,
            headline="The shop reports stock, but remaining entitlement could not be verified.",
            reasons=[
                "A complete, verified draw history for this member and commodity is not available.",
                "The application must not invent a remaining quantity.",
                *notes,
            ],
            cannot_guarantee=[
                "The transaction may fail at the shop if the entitlement record is incomplete.",
            ],
            **base_kwargs,
        )

    if data.remaining_quantity <= 0:
        return PortabilityResult(
            decision=Decision.NOT_SUPPORTED,
            eligible_to_proceed=False,
            travel_recommended=False,
            headline="No remaining quantity is recorded for this commodity and period.",
            reasons=["The verified record shows no remaining quantity for the current synthetic period."],
            cannot_guarantee=["This demo does not determine legal eligibility."],
            **base_kwargs,
        )

    return PortabilityResult(
        decision=Decision.ELIGIBLE,
        eligible_to_proceed=True,
        travel_recommended=True,
        headline=(
            f"{commodity_meta.get('name', data.commodity_code)} is verified available at the destination shop "
            f"and the synthetic entitlement record is complete."
        ),
        reasons=[
            f"Verified remaining quantity: {data.remaining_quantity:g} {data.remaining_unit or ''}".strip(),
            "Destination stock state is verified and current.",
            *notes,
        ],
        cannot_guarantee=[
            "The shop may still apply its own verification and the transaction is not guaranteed.",
            "This answer is derived from synthetic demonstration rules, not current law.",
        ],
        **base_kwargs,
    )
