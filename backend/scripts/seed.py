"""Deterministic synthetic seed data for RationSaathi.

Everything here is fictional. No real household, identity reference, shop,
receipt, entitlement rate, stock state or legal deadline is represented.
"""

from __future__ import annotations

import json
import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.orm import Session as DbSession  # noqa: E402

from app.db import Base, create_all, get_engine, get_session_factory, utcnow  # noqa: E402
from app.models import (  # noqa: E402
    AuditEvent,
    Commodity,
    Grievance,
    GrievanceAssignment,
    GrievanceEvent,
    Household,
    Member,
    MemberConsent,
    MemberEntitlement,
    OfflineDraft,
    RationShop,
    RecordSnapshot,
    RuleVersion,
    ServiceLevelPolicy,
    StockObservation,
)

RULES_PATH = Path(__file__).resolve().parent.parent / "app" / "rules" / "portability_rules.json"
DRAFT_ID = "draft-seed-1042"


def seed_all(db: DbSession, now=None) -> dict:
    now = now or utcnow()
    rules = json.loads(RULES_PATH.read_text(encoding="utf-8"))

    commodities = [
        Commodity(code="RICE", name="Rice", unit="kg"),
        Commodity(code="WHEAT", name="Wheat flour", unit="kg"),
        Commodity(code="SUGAR", name="Sugar", unit="kg"),
        Commodity(code="KEROSENE", name="Kerosene (synthetic demo)", unit="litre"),
    ]
    db.add_all(commodities)

    shop_a = RationShop(
        id="shop-syn-02",
        name="SYN Shop 02 — Destination (synthetic)",
        jurisdiction_code="SYN-GJ",
        address_label="Synthetic Market Road, Demo Ward 4",
    )
    shop_b = RationShop(
        id="shop-syn-07",
        name="SYN Shop 07 — Alternate (synthetic)",
        jurisdiction_code="SYN-GJ",
        address_label="Synthetic Station Lane, Demo Ward 9",
    )
    db.add_all([shop_a, shop_b])

    house_a = Household(
        id="hh-syn-1042",
        reference="SYN-HH-1042",
        label="Synthetic Sharma migrant household",
        home_state="Synthetic Maharashtra",
        home_jurisdiction_code="SYN-MH",
        destination_state="Synthetic Gujarat",
        destination_jurisdiction_code="SYN-GJ",
        destination_shop_id=shop_a.id,
        provenance="SYNTHETIC_DEMO",
        last_verified_at=now - timedelta(days=3),
        last_synced_at=now - timedelta(hours=2),
        is_synthetic=True,
    )
    house_b = Household(
        id="hh-syn-2077",
        reference="SYN-HH-2077",
        label="Synthetic Fernandes household (handover test)",
        home_state="Synthetic Bihar",
        home_jurisdiction_code="SYN-BR",
        destination_state="Synthetic Gujarat",
        destination_jurisdiction_code="SYN-GJ",
        destination_shop_id=shop_b.id,
        provenance="SYNTHETIC_DEMO",
        last_verified_at=now - timedelta(days=10),
        last_synced_at=now - timedelta(days=1),
        is_synthetic=True,
    )
    db.add_all([house_a, house_b])

    members = [
        # Household A — five members
        Member(
            id="mem-a1",
            household_id=house_a.id,
            display_alias="Sunita (head)",
            full_name="Sunita Devi",
            age=46,
            membership_status="ACTIVE",
            relationship="Head of household",
            verification_state="VERIFIED_SYNTHETIC",
            provenance="OFFICIAL_LAST_SYNCED",
            consent_state="RECORDED",
            is_head=True,
            is_absent=True,
            document_name="Sunita Devi",
            document_age=46,
            document_ref="SYN-ID-A1",
            document_provenance="OFFICIAL_LAST_SYNCED",
            last_verified_at=now - timedelta(days=3),
        ),
        Member(
            id="mem-a2",
            household_id=house_a.id,
            display_alias="Ramesh",
            full_name="Ramesh Kumr",
            age=34,
            membership_status="ACTIVE",
            relationship="Spouse",
            verification_state="MISMATCH_FLAGGED",
            provenance="HOUSEHOLD_REPORTED",
            consent_state="RECORDED",
            is_absent=False,
            document_name="Ramesh Kumar",
            document_age=36,
            document_ref="SYN-ID-A2",
            document_provenance="FACILITATOR_ENTERED",
            last_verified_at=now - timedelta(days=8),
        ),
        Member(
            id="mem-a3",
            household_id=house_a.id,
            display_alias="Meena",
            full_name="Meena Kumari",
            age=29,
            membership_status="ACTIVE",
            relationship="Sister",
            verification_state="INCOMPLETE",
            provenance="HOUSEHOLD_REPORTED",
            consent_state="RECORDED",
            document_ref=None,
            document_provenance=None,
            last_verified_at=None,
        ),
        Member(
            id="mem-a4",
            household_id=house_a.id,
            display_alias="Arjun",
            full_name="Arjun Kumar",
            age=11,
            age_band="6-14",
            membership_status="ACTIVE",
            relationship="Child",
            verification_state="VERIFIED_SYNTHETIC",
            provenance="OFFICIAL_LAST_SYNCED",
            consent_state="REPRESENTED",
            is_dependent=True,
            document_name="Arjun Kumar",
            document_age=11,
            document_ref="SYN-ID-A4",
            document_provenance="OFFICIAL_LAST_SYNCED",
            last_verified_at=now - timedelta(days=3),
        ),
        Member(
            id="mem-a5",
            household_id=house_a.id,
            display_alias="Lakshmi",
            full_name="Lakshmi Devi",
            age=67,
            membership_status="ACTIVE",
            relationship="Mother",
            verification_state="VERIFIED_SYNTHETIC",
            provenance="OFFICIAL_LAST_SYNCED",
            consent_state="REPRESENTED",
            is_dependent=True,
            document_name="Lakshmi Devi",
            document_age=67,
            document_ref="SYN-ID-A5",
            document_provenance="OFFICIAL_LAST_SYNCED",
            last_verified_at=now - timedelta(days=3),
        ),
        # Household B — unrelated handover test
        Member(
            id="mem-b1",
            household_id=house_b.id,
            display_alias="Maria",
            full_name="Maria Fernandes",
            age=38,
            membership_status="ACTIVE",
            relationship="Head of household",
            verification_state="VERIFIED_SYNTHETIC",
            provenance="SYNTHETIC_DEMO",
            consent_state="RECORDED",
            is_head=True,
            document_name="Maria Fernandes",
            document_age=38,
            document_ref="SYN-ID-B1",
            document_provenance="SYNTHETIC_DEMO",
            last_verified_at=now - timedelta(days=10),
        ),
        Member(
            id="mem-b2",
            household_id=house_b.id,
            display_alias="Joel",
            full_name="Joel Fernandes",
            age=16,
            membership_status="ACTIVE",
            relationship="Child",
            verification_state="VERIFIED_SYNTHETIC",
            provenance="SYNTHETIC_DEMO",
            consent_state="REPRESENTED",
            is_dependent=True,
            document_name="Joel Fernandes",
            document_age=16,
            document_ref="SYN-ID-B2",
            document_provenance="SYNTHETIC_DEMO",
        ),
        Member(
            id="mem-b3",
            household_id=house_b.id,
            display_alias="Ana",
            full_name="Ana Fernandes",
            age=70,
            membership_status="ACTIVE",
            relationship="Mother",
            verification_state="VERIFIED_SYNTHETIC",
            provenance="SYNTHETIC_DEMO",
            consent_state="REPRESENTED",
            is_dependent=True,
        ),
    ]
    db.add_all(members)
    db.flush()

    db.add_all(
        [
            MemberConsent(member_id="mem-a1", scope="self_service", granted=True, provenance="SYNTHETIC_DEMO"),
            MemberConsent(member_id="mem-a2", scope="self_service", granted=True, provenance="SYNTHETIC_DEMO"),
            MemberConsent(member_id="mem-a3", scope="self_service", granted=True, provenance="SYNTHETIC_DEMO"),
            MemberConsent(
                member_id="mem-a4",
                scope="represented_by_mem_a2",
                granted=True,
                provenance="SYNTHETIC_DEMO",
            ),
            MemberConsent(
                member_id="mem-a5",
                scope="represented_by_mem_a2",
                granted=True,
                provenance="SYNTHETIC_DEMO",
            ),
            MemberConsent(member_id="mem-b1", scope="self_service", granted=True, provenance="SYNTHETIC_DEMO"),
            MemberConsent(member_id="mem-b2", scope="represented_by_mem_b1", granted=True, provenance="SYNTHETIC_DEMO"),
            MemberConsent(member_id="mem-b3", scope="represented_by_mem_b1", granted=True, provenance="SYNTHETIC_DEMO"),
        ]
    )

    def ent(member_id: str, commodity: str, unit: str, entitled: float | None, drawn: float | None,
            provenance: str, remaining: float | None = None, verified: bool = False) -> MemberEntitlement:
        period = "2026-10"
        return MemberEntitlement(
            id=f"ent-{member_id}-{commodity.lower()}-{period}",
            member_id=member_id,
            commodity_code=commodity,
            period=period,
            entitled_qty=entitled,
            drawn_qty=drawn,
            remaining_qty=remaining,
            unit=unit,
            provenance=provenance,
            verification_status="VERIFIED" if verified else "SYNTHETIC_FIXTURE_UNVERIFIED",
            jurisdiction="SYN-GJ",
            rules_version="synthetic-2026.1",
            source_ref="SYN-FIXTURE-2026-10" if not verified else "SYN-SYNC-0042",
            last_verified_at=(now - timedelta(hours=2)) if verified else None,
        )

    db.flush()

    db.add_all(
        [
            # Ramesh: one official-last-synced, complete entitlement (used for the "eligible" pathway).
            ent("mem-a2", "RICE", "kg", 5, 2, "OFFICIAL_LAST_SYNCED", 3, True),
            ent("mem-a2", "WHEAT", "kg", 3, 0, "SYNTHETIC_DEMO"),
            ent("mem-a2", "SUGAR", "kg", 1, 1, "SYNTHETIC_DEMO"),
            # Sunita (absent head)
            ent("mem-a1", "RICE", "kg", 5, 5, "OFFICIAL_LAST_SYNCED", 0, True),
            ent("mem-a1", "WHEAT", "kg", 3, None, "OFFICIAL_LAST_SYNCED"),
            # Meena: deliberately incomplete draw history -> remaining must not be invented.
            ent("mem-a3", "RICE", "kg", 5, 1, "SYNTHETIC_DEMO"),
            ent("mem-a3", "WHEAT", "kg", 3, None, "HOUSEHOLD_REPORTED"),
            # Children / elder dependents
            ent("mem-a4", "RICE", "kg", 5, 0, "SYNTHETIC_DEMO"),
            ent("mem-a4", "WHEAT", "kg", 3, 1, "SYNTHETIC_DEMO"),
            ent("mem-a5", "RICE", "kg", 5, 2, "SYNTHETIC_DEMO"),
            ent("mem-a5", "SUGAR", "kg", 1, 0, "SYNTHETIC_DEMO"),
            # Household B
            ent("mem-b1", "RICE", "kg", 5, 1, "SYNTHETIC_DEMO"),
            ent("mem-b2", "RICE", "kg", 5, 0, "SYNTHETIC_DEMO"),
            ent("mem-b3", "WHEAT", "kg", 3, 0, "SYNTHETIC_DEMO"),
        ]
    )

    db.add(
        RecordSnapshot(
            id="snap-seed-ramesh",
            household_id=house_a.id,
            member_id="mem-a2",
            reason="BASELINE_PRESERVED",
            payload={
                "member_id": "mem-a2",
                "name": "Ramesh Kumr",
                "age": 34,
                "entitlement_links": ["ent-mem-a2-rice-2026-10", "ent-mem-a2-wheat-2026-10", "ent-mem-a2-sugar-2026-10"],
                "note": "Original synthetic member record preserved before any correction attempt.",
            },
        )
    )

    # Stock observations: one reported out of stock, one verified, one stale, one unknown.
    db.add_all(
        [
            StockObservation(
                id="stock-a-rice",
                shop_id=shop_a.id,
                commodity_code="RICE",
                state="OUT_OF_STOCK_REPORTED",
                observed_at=now - timedelta(hours=6),
                source="Destination shop counter report (synthetic)",
                source_ref="SYN-STK-9001",
                provenance="HOUSEHOLD_REPORTED",
                note="Reported by the shop counter; not independently verified.",
            ),
            StockObservation(
                id="stock-a-wheat",
                shop_id=shop_a.id,
                commodity_code="WHEAT",
                state="AVAILABLE_VERIFIED",
                observed_at=now - timedelta(hours=2),
                source="Synthetic stock sync",
                source_ref="SYN-STK-9002",
                provenance="OFFICIAL_VERIFIED",
                note="Verified synthetic stock record.",
            ),
            StockObservation(
                id="stock-a-sugar",
                shop_id=shop_a.id,
                commodity_code="SUGAR",
                state="AVAILABLE_VERIFIED",
                observed_at=now - timedelta(hours=30),
                source="Synthetic stock sync",
                source_ref="SYN-STK-9003",
                provenance="OFFICIAL_LAST_SYNCED",
                note="Older than the configured freshness window.",
            ),
            StockObservation(
                id="stock-b-rice",
                shop_id=shop_b.id,
                commodity_code="RICE",
                state="UNKNOWN",
                observed_at=now - timedelta(hours=12),
                source="No confirmed update (synthetic)",
                provenance="UNKNOWN",
                note="Alternate shop has not reported stock.",
            ),
            StockObservation(
                id="stock-a-kerosene",
                shop_id=shop_a.id,
                commodity_code="KEROSENE",
                state="SOURCE_UNAVAILABLE",
                observed_at=now - timedelta(hours=5),
                source="Synthetic stock source offline",
                provenance="UNKNOWN",
            ),
        ]
    )

    db.add(
        RuleVersion(
            id="rule-portability-2026-1",
            scope="portability",
            version=rules["version"],
            effective_from=now - timedelta(days=30),
            source_label=rules["source_label"],
            is_synthetic=True,
            payload=rules,
        )
    )

    db.add_all(
        [
            ServiceLevelPolicy(
                id="sla-commodity-28",
                category="COMMODITY_UNAVAILABLE",
                jurisdiction_code="SYN-GJ",
                days=28,
                version="synthetic-sla-2026.1",
                source_label="SYNTHETIC DEMO POLICY (28 days) — illustrative only, not a legal deadline",
                verified=True,
                is_synthetic=True,
            ),
            ServiceLevelPolicy(
                id="sla-correction-21",
                category="RECORD_CORRECTION",
                jurisdiction_code="SYN-GJ",
                days=21,
                version="synthetic-sla-2026.1",
                source_label="SYNTHETIC DEMO POLICY (21 days) — illustrative only, not a legal deadline",
                verified=True,
                is_synthetic=True,
            ),
        ]
    )

    db.flush()

    # 21-day-old grievance: deadline deliberately unverified.
    g1 = Grievance(
        id="grv-21day",
        household_id=house_a.id,
        member_id="mem-a2",
        category="COMMODITY_UNAVAILABLE",
        subject="Synthetic: commodity unavailable at destination shop",
        filed_at=now - timedelta(days=21),
        provenance="SYNTHETIC_DEMO",
        official_receipt_number="SYN-RCPT-GRV-0021",
        responsible_office=None,
        office_verified=False,
        assigned_officer=None,
        status="FILED",
        last_status_update=now - timedelta(days=21),
        sla_policy_id=None,
        deadline_verified=False,
        deadline_at=None,
        response_summary=None,
        is_synthetic=True,
    )
    g2 = Grievance(
        id="grv-overdue",
        household_id=house_a.id,
        member_id="mem-a2",
        category="COMMODITY_UNAVAILABLE",
        subject="Synthetic: no response after configured service period",
        filed_at=now - timedelta(days=40),
        provenance="SYNTHETIC_DEMO",
        official_receipt_number="SYN-RCPT-GRV-0034",
        responsible_office="Synthetic District Supply Office (demo)",
        office_verified=True,
        assigned_officer=None,
        status="FILED",
        last_status_update=now - timedelta(days=40),
        sla_policy_id="sla-commodity-28",
        deadline_verified=True,
        deadline_at=now - timedelta(days=12),
        response_summary=None,
        deadline_source_label="SYNTHETIC DEMO POLICY (28 days) — illustrative only, not a legal deadline",
        is_synthetic=True,
    )
    g3 = Grievance(
        id="grv-resolved",
        household_id=house_a.id,
        member_id="mem-a2",
        category="RECORD_CORRECTION",
        subject="Synthetic: spelling correction acknowledged",
        filed_at=now - timedelta(days=30),
        provenance="SYNTHETIC_DEMO",
        official_receipt_number="SYN-RCPT-GRV-0041",
        responsible_office="Synthetic District Supply Office (demo)",
        office_verified=True,
        assigned_officer="Synthetic Officer (demo)",
        status="RESOLVED",
        last_status_update=now - timedelta(days=20),
        sla_policy_id="sla-correction-21",
        deadline_verified=True,
        deadline_at=now - timedelta(days=9),
        response_summary="Synthetic response: correction request reviewed and record updated in the demo system.",
        resolution_summary="Synthetic resolution recorded for demonstration.",
        is_synthetic=True,
    )
    g4 = Grievance(
        id="grv-handover-b",
        household_id=house_b.id,
        member_id="mem-b1",
        category="COMMODITY_UNAVAILABLE",
        subject="Synthetic household B grievance (handover isolation test)",
        filed_at=now - timedelta(days=9),
        provenance="SYNTHETIC_DEMO",
        official_receipt_number="SYN-RCPT-GRV-B009",
        responsible_office="Synthetic District Supply Office (demo)",
        office_verified=True,
        status="FILED",
        last_status_update=now - timedelta(days=9),
        sla_policy_id="sla-commodity-28",
        deadline_verified=True,
        deadline_at=now + timedelta(days=19),
        is_synthetic=True,
    )
    db.add_all([g1, g2, g3, g4])
    db.add_all(
        [
            GrievanceEvent(
                id="evt-g1-filed",
                grievance_id=g1.id,
                event_type="FILED",
                occurred_at=now - timedelta(days=21),
                detail={"provenance": "SYNTHETIC_DEMO", "official_receipt": "SYN-RCPT-GRV-0021"},
            ),
            GrievanceEvent(
                id="evt-g1-check",
                grievance_id=g1.id,
                event_type="STATUS_CHECKED_NO_RESPONSE",
                occurred_at=now - timedelta(days=7),
                detail={"response_found": False, "note": "No recorded response in the synthetic case file."},
            ),
            GrievanceEvent(
                id="evt-g2-filed",
                grievance_id=g2.id,
                event_type="FILED",
                occurred_at=now - timedelta(days=40),
                detail={"provenance": "SYNTHETIC_DEMO"},
            ),
            GrievanceEvent(
                id="evt-g3-filed",
                grievance_id=g3.id,
                event_type="FILED",
                occurred_at=now - timedelta(days=30),
                detail={"provenance": "SYNTHETIC_DEMO"},
            ),
            GrievanceEvent(
                id="evt-g3-resolved",
                grievance_id=g3.id,
                event_type="RESOLVED",
                occurred_at=now - timedelta(days=20),
                detail={"note": "Synthetic resolution."},
            ),
            GrievanceEvent(
                id="evt-g4-filed",
                grievance_id=g4.id,
                event_type="FILED",
                occurred_at=now - timedelta(days=9),
                detail={"provenance": "SYNTHETIC_DEMO"},
            ),
        ]
    )
    db.add(
        GrievanceAssignment(
            id="assign-g2",
            grievance_id=g2.id,
            office="Synthetic District Supply Office (demo)",
            officer_placeholder=None,
            verified=True,
            assigned_at=now - timedelta(days=39),
        )
    )

    db.add(
        OfflineDraft(
            id=DRAFT_ID,
            draft_ref="RS-D-1042",
            household_id=house_a.id,
            member_id="mem-a2",
            kind="CORRECTION",
            state="DRAFT_NOT_SUBMITTED",
            payload={
                "label": "DRAFT — NOT SUBMITTED",
                "operation": "UPDATE_FIELD",
                "fields": {"name": "Ramesh Kumar", "age": 36},
                "evidence": ["household_reference"],
                "prepared_at": "Synthetic assisted-service centre (demo)",
                "note": "Prepared by a facilitator. Not sent to any official system.",
            },
            version=2,
            idempotency_key="seed-draft-1042",
            created_by_session=None,
        )
    )

    db.add(
        AuditEvent(
            id="audit-seed",
            action="demo_seeded",
            actor_role="SYSTEM",
            household_ref=None,
            outcome="OK",
            detail={"dataset": "synthetic-2026.1", "note": "All records are fictional demonstration fixtures."},
        )
    )

    db.flush()
    return {
        "households": 2,
        "members": len(members),
        "entitlements": 14,
        "drafts": 1,
        "grievances": 4,
        "stock_observations": 5,
        "seeded_at": now.isoformat(),
    }


def reset_and_seed() -> dict:
    engine = get_engine()
    from app import models  # noqa: F401

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    factory = get_session_factory()
    with factory() as db:
        summary = seed_all(db)
        db.commit()
    return summary


def main() -> None:
    summary = reset_and_seed()
    print("Seeded synthetic demo data:", summary)


if __name__ == "__main__":
    main()
