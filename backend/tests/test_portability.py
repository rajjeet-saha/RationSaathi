import json
from datetime import timedelta
from pathlib import Path

from app.rules.portability import PortabilityInput, StockFact, evaluate_portability
from app.db import utcnow

RULES = json.loads((Path(__file__).resolve().parent.parent / "app" / "rules" / "portability_rules.json").read_text())
NOW = utcnow()


def make_input(**overrides):
    base = dict(
        home_code="SYN-MH",
        destination_code="SYN-GJ",
        commodity_code="WHEAT",
        member_alias="Ramesh",
        authorization_ok=True,
        identity_evidence_present=True,
        remaining_verified=True,
        remaining_quantity=3,
        remaining_unit="kg",
        stock=StockFact(
            state="AVAILABLE_VERIFIED",
            observed_at=NOW - timedelta(hours=2),
            source="Synthetic stock sync",
            provenance="OFFICIAL_VERIFIED",
        ),
        network_online=True,
        now=NOW,
    )
    base.update(overrides)
    return PortabilityInput(**base)


def test_verified_stock_and_complete_entitlement_is_eligible():
    result = evaluate_portability(RULES, make_input())
    assert result.decision == "ELIGIBLE_TO_PROCEED"
    assert result.eligible_to_proceed is True
    assert result.travel_recommended is True
    assert result.rule["is_synthetic"] is True
    assert "not current law" in " ".join(result.cannot_guarantee).lower()


def test_reported_out_of_stock_blocks_travel_and_promises_nothing():
    result = evaluate_portability(
        RULES,
        make_input(stock=StockFact("OUT_OF_STOCK_REPORTED", NOW - timedelta(hours=1), "Counter report", "HOUSEHOLD_REPORTED")),
    )
    assert result.decision == "MORE_INFORMATION_REQUIRED"
    assert result.travel_recommended is False
    assert result.eligible_to_proceed is False
    assert result.stock["state"] == "OUT_OF_STOCK_REPORTED"
    text = " ".join(result.cannot_guarantee).lower()
    assert "not a guarantee" in text or "no alternative" in text
    assert all("guarantee" not in pathway["detail"].lower() for pathway in result.alternative_pathways)


def test_verified_out_of_stock_is_still_not_a_promise_about_other_shops():
    result = evaluate_portability(
        RULES,
        make_input(stock=StockFact("OUT_OF_STOCK_VERIFIED", NOW - timedelta(hours=1), "Synthetic sync", "OFFICIAL_VERIFIED")),
    )
    assert result.decision == "MORE_INFORMATION_REQUIRED"
    assert "verified unavailable" in result.headline.lower()
    assert result.travel_recommended is False


def test_stale_stock_is_downgraded_and_travel_is_not_recommended():
    result = evaluate_portability(
        RULES,
        make_input(stock=StockFact("AVAILABLE_VERIFIED", NOW - timedelta(hours=30), "Synthetic sync", "OFFICIAL_LAST_SYNCED")),
    )
    assert result.decision == "CANNOT_DETERMINE_FROM_AVAILABLE_DATA"
    assert result.stock["state"] == "STALE"
    assert result.travel_recommended is False
    assert "stale" in result.headline.lower()


def test_unknown_stock_cannot_be_determined():
    result = evaluate_portability(
        RULES,
        make_input(stock=StockFact("UNKNOWN", NOW - timedelta(hours=3), "No update", "UNKNOWN")),
    )
    assert result.decision == "CANNOT_DETERMINE_FROM_AVAILABLE_DATA"
    assert result.travel_recommended is False


def test_missing_stock_source_cannot_be_determined():
    result = evaluate_portability(RULES, make_input(stock=None))
    assert result.decision == "CANNOT_DETERMINE_FROM_AVAILABLE_DATA"
    assert result.stock["state"] == "SOURCE_UNAVAILABLE"
    assert result.travel_recommended is False


def test_reported_available_is_only_potential():
    result = evaluate_portability(
        RULES,
        make_input(stock=StockFact("REPORTED_AVAILABLE", NOW - timedelta(hours=2), "Household report", "HOUSEHOLD_REPORTED")),
    )
    assert result.decision == "POTENTIALLY_ELIGIBLE_VERIFICATION_REQUIRED"
    assert result.travel_recommended is False


def test_unverified_remaining_quantity_is_not_invented():
    result = evaluate_portability(RULES, make_input(remaining_verified=False, remaining_quantity=None))
    assert result.decision == "POTENTIALLY_ELIGIBLE_VERIFICATION_REQUIRED"
    assert result.travel_recommended is False
    assert "remaining entitlement could not be verified" in result.headline.lower()


def test_zero_remaining_quantity_is_not_eligible():
    result = evaluate_portability(RULES, make_input(remaining_quantity=0))
    assert result.decision == "NOT_SUPPORTED_BY_CONFIGURED_RULES"
    assert result.eligible_to_proceed is False


def test_missing_identity_evidence_requires_more_information():
    result = evaluate_portability(RULES, make_input(identity_evidence_present=False))
    assert result.decision == "MORE_INFORMATION_REQUIRED"
    assert result.travel_recommended is False


def test_unconfigured_state_pair_fails_safe():
    result = evaluate_portability(RULES, make_input(home_code="SYN-XX", destination_code="SYN-GJ"))
    assert result.decision == "CANNOT_DETERMINE_FROM_AVAILABLE_DATA"
    assert result.travel_recommended is False
    assert result.rule["is_synthetic"] is True


def test_commodity_not_covered_by_pair_is_not_supported():
    result = evaluate_portability(
        RULES,
        make_input(home_code="SYN-BR", destination_code="SYN-GJ", commodity_code="SUGAR"),
    )
    assert result.decision == "NOT_SUPPORTED_BY_CONFIGURED_RULES"
    assert result.eligible_to_proceed is False


def test_freshness_window_boundary_is_respected():
    fresh = evaluate_portability(
        RULES,
        make_input(stock=StockFact("AVAILABLE_VERIFIED", NOW - timedelta(hours=23), "Synthetic sync", "OFFICIAL_VERIFIED")),
    )
    stale = evaluate_portability(
        RULES,
        make_input(stock=StockFact("AVAILABLE_VERIFIED", NOW - timedelta(hours=25), "Synthetic sync", "OFFICIAL_VERIFIED")),
    )
    assert fresh.stock["state"] == "AVAILABLE_VERIFIED"
    assert stale.stock["state"] == "STALE"
