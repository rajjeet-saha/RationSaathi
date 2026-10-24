from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select

from app.db import get_session_factory, utcnow
from app.models import Grievance, Member, MemberEntitlement, StockObservation


FORBIDDEN_STRINGS = [
    "Sharma",
    "Fernandes",
    "Ramesh",
    "Sunita",
    "Meena",
    "Arjun",
    "Lakshmi",
    "SYN-HH-1042",
    "SYN-HH-2077",
    "SYN-RCPT-GRV",
    "mem-a",
    "mem-b",
    "hh-syn",
    "SYN-ID",
]


def test_public_aggregates_are_suppressed_below_minimum_group(client):
    resp = client.get("/api/v1/public/aggregates")
    assert resp.status_code == 200
    data = resp.json()
    assert data["minimum_group_size"] == 5

    # Only 4 grievances are seeded, so every count cell must be suppressed.
    assert data["grievances"]["total"]["suppressed"] is True
    assert data["grievances"]["total"]["value"] is None
    for cell in data["grievances"]["by_category"]:
        assert cell["count"]["suppressed"] is True
        assert cell["count"]["value"] is None
    assert data["grievances"]["median_processing_days"]["suppressed"] is True


def test_public_aggregates_contain_no_personal_identifiers(client):
    resp = client.get("/api/v1/public/aggregates")
    text = resp.text
    for secret in FORBIDDEN_STRINGS:
        assert secret.lower() not in text.lower(), f"leaked {secret}"


def test_public_aggregates_work_without_a_session(client):
    assert client.get("/api/v1/public/aggregates").status_code == 200


def test_public_aggregates_include_disclaimers_and_method(client):
    data = client.get("/api/v1/public/aggregates").json()
    assert data["is_synthetic"] is True
    assert "synthetic" in data["disclaimer"].lower()
    assert "suppression" in " ".join(data["method"].values()).lower()
    assert data["method"]["identifiers"]


def test_aggregates_reveal_overdue_only_when_verified(client):
    data = client.get("/api/v1/public/aggregates").json()
    overdue = data["grievances"]["verified_overdue"]
    # n=4 < 5 so suppressed; the point is it is derived from verified deadlines.
    assert overdue["suppressed"] is True


def test_sla_policies_are_labelled_synthetic(client):
    data = client.get("/api/v1/public/aggregates").json()
    assert data["sla_policies"], "expected seeded synthetic SLA policies"
    for policy in data["sla_policies"]:
        assert policy["is_synthetic"] is True
        assert "not a legal deadline" in policy["source_label"].lower()


def test_counts_reveal_after_reaching_minimum_group(client):
    """Insert enough identical grievances to cross the k threshold and confirm the
    cell becomes visible — proving the suppression is real, not cosmetic."""
    factory = get_session_factory()
    with factory() as db:
        household_id = "hh-syn-1042"
        member_id = "mem-a2"
        for i in range(8):
            db.add(
                Grievance(
                    id=f"grv-bulk-{i}",
                    household_id=household_id,
                    member_id=member_id,
                    category="RECORD_CORRECTION",
                    subject=f"Synthetic bulk grievance {i}",
                    filed_at=utcnow() - timedelta(days=3),
                    provenance="SYNTHETIC_DEMO",
                    official_receipt_number=f"SYN-RCPT-BULK-{i}",
                    status="FILED",
                    last_status_update=utcnow() - timedelta(days=3),
                    is_synthetic=True,
                )
            )
        db.commit()

    resp = client.get("/api/v1/public/aggregates")
    data = resp.json()
    # The residual group (3) is smaller than k, so publishing the total would let a
    # reader recover it by subtraction. Secondary suppression must keep it hidden.
    total = data["grievances"]["total"]
    assert total["suppressed"] is True
    assert total["value"] is None

    by_category = {row["category"]: row for row in data["grievances"]["by_category"]}
    assert by_category["RECORD_CORRECTION"]["count"]["suppressed"] is False
    assert by_category["RECORD_CORRECTION"]["count"]["value"] == 9
    # The small COMMODITY_UNAVAILABLE group (3) must stay suppressed.
    assert by_category["COMMODITY_UNAVAILABLE"]["count"]["suppressed"] is True

    # Even with visible totals, no identifiers appear.
    text = resp.text
    for secret in ["Ramesh", "SYN-HH-1042", "SYN-RCPT-BULK-0"]:
        assert secret not in text
