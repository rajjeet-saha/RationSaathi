"""Deterministic evaluation harness for the correction safety engine.

The dataset is small and synthetic. A 100% result here proves only that the
seeded entitlement-removing cases are detected; it is not a claim of universal
real-world protection.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain import RiskLevel
from app.rules.correction import (
    ActorContext,
    CorrectionSimulation,
    EntitlementFact,
    HouseholdFact,
    MemberFact,
    ProposedChange,
    simulate_correction,
)

ENTITLEMENTS_A2 = (
    EntitlementFact("ent-a2-rice", "RICE", "2026-10", 5, 2, 3, "OFFICIAL_LAST_SYNCED"),
    EntitlementFact("ent-a2-wheat", "WHEAT", "2026-10", 3, 0, None, "SYNTHETIC_DEMO"),
    EntitlementFact("ent-a2-sugar", "SUGAR", "2026-10", 1, 1, 0, "SYNTHETIC_DEMO"),
)
ENTITLEMENTS_A3 = (
    EntitlementFact("ent-a3-rice", "RICE", "2026-10", 5, 1, None, "SYNTHETIC_DEMO"),
)

HOUSEHOLD = HouseholdFact(
    id="hh-eval",
    reference="SYN-HH-EVAL",
    members=(
        MemberFact(
            id="mem-a2",
            alias="Ramesh",
            name="Ramesh Kumr",
            age=34,
            membership_status="ACTIVE",
            document_name="Ramesh Kumar",
            document_age=36,
            document_ref="SYN-ID-A2",
            entitlements=ENTITLEMENTS_A2,
        ),
        MemberFact(
            id="mem-a3",
            alias="Meena",
            name="Meena Kumari",
            age=29,
            membership_status="ACTIVE",
            document_ref=None,
            entitlements=ENTITLEMENTS_A3,
        ),
        MemberFact(
            id="mem-head",
            alias="Head",
            name="Sunita Devi",
            age=46,
            membership_status="ACTIVE",
            is_head=True,
            entitlements=(),
        ),
    ),
)

SELF_ACTOR = ActorContext(
    role="MEMBER",
    session_member_id="mem-a2",
    can_change_identity=True,
    can_change_membership=False,
    head_absent=True,
)
FACILITATOR_ACTOR = ActorContext(
    role="FACILITATOR",
    session_member_id=None,
    can_change_identity=False,
    can_change_membership=False,
)
OTHER_MEMBER_ACTOR = ActorContext(
    role="MEMBER",
    session_member_id="mem-head",
    can_change_identity=True,
    can_change_membership=False,
)

FULL_EVIDENCE = ["identity_reference", "household_reference", "member_confirmation"]


@dataclass(frozen=True)
class Case:
    key: str
    label: str
    expected: str  # HARMFUL | HARMLESS | UNCERTAIN
    proposed: ProposedChange
    actor: ActorContext
    evidence: list[str]


CASES: list[Case] = [
    Case(
        "spelling-correction",
        "Harmless spelling correction preserves the member",
        "HARMLESS",
        ProposedChange("UPDATE_FIELD", "mem-a2", fields={"name": "Ramesh Kumar"}),
        SELF_ACTOR,
        FULL_EVIDENCE,
    ),
    Case(
        "age-correction",
        "Harmless age correction supported by the synthetic document",
        "HARMLESS",
        ProposedChange("UPDATE_FIELD", "mem-a2", fields={"age": 36}),
        SELF_ACTOR,
        FULL_EVIDENCE,
    ),
    Case(
        "delete-member",
        "Deletion removes one member and their entitlement links",
        "HARMFUL",
        ProposedChange("DELETE_MEMBER", "mem-a2"),
        SELF_ACTOR,
        FULL_EVIDENCE,
    ),
    Case(
        "replace-member",
        "Delete-and-recreate removes the original member",
        "HARMFUL",
        ProposedChange(
            "REPLACE_MEMBER",
            "mem-a2",
            new_member={"name": "Ramesh Kumar", "age": 36},
        ),
        SELF_ACTOR,
        FULL_EVIDENCE,
    ),
    Case(
        "membership-removal",
        "Membership-status removal would deactivate the member",
        "HARMFUL",
        ProposedChange("UPDATE_FIELD", "mem-a2", fields={"membership_status": "REMOVED"}),
        SELF_ACTOR,
        FULL_EVIDENCE,
    ),
    Case(
        "duplicate-creation",
        "Duplicate creation splits one person into two records",
        "HARMFUL",
        ProposedChange("CREATE_MEMBER", "mem-a2", new_member={"name": "Ramesh Kumar", "age": 36}),
        SELF_ACTOR,
        FULL_EVIDENCE,
    ),
    Case(
        "missing-member-new-applicant",
        "A missing member is incorrectly treated as a new applicant",
        "HARMFUL",
        ProposedChange("CREATE_MEMBER", "mem-missing", new_member={"name": "New Person", "age": 30}),
        SELF_ACTOR,
        FULL_EVIDENCE,
    ),
    Case(
        "merge-removes-links",
        "Merging duplicate records removes entitlement links",
        "HARMFUL",
        ProposedChange("MERGE_DUPLICATE", "mem-a2", merge_into_member_id="mem-a3"),
        SELF_ACTOR,
        FULL_EVIDENCE,
    ),
    Case(
        "unauthorised-edit",
        "One adult attempts to edit another adult's record",
        "HARMFUL",
        ProposedChange("UPDATE_FIELD", "mem-a2", fields={"name": "Ramesh Kumar"}),
        OTHER_MEMBER_ACTOR,
        FULL_EVIDENCE,
    ),
    Case(
        "facilitator-edit",
        "Facilitator attempts to edit identity fields",
        "HARMFUL",
        ProposedChange("UPDATE_FIELD", "mem-a2", fields={"name": "Ramesh Kumar"}),
        FACILITATOR_ACTOR,
        FULL_EVIDENCE,
    ),
    Case(
        "conflicting-evidence",
        "Conflicting age evidence leaves the correct value uncertain",
        "UNCERTAIN",
        ProposedChange("UPDATE_FIELD", "mem-a2", fields={"age": 40}),
        SELF_ACTOR,
        FULL_EVIDENCE,
    ),
    Case(
        "different-name",
        "Substantially different name requires verification",
        "UNCERTAIN",
        ProposedChange("UPDATE_FIELD", "mem-a2", fields={"name": "Rajesh Verma"}),
        SELF_ACTOR,
        FULL_EVIDENCE,
    ),
    Case(
        "missing-evidence",
        "Evidence is missing for a spelling correction",
        "UNCERTAIN",
        ProposedChange("UPDATE_FIELD", "mem-a2", fields={"name": "Ramesh Kumar"}),
        SELF_ACTOR,
        [],
    ),
    Case(
        "membership-change",
        "Membership status change requires household authority",
        "UNCERTAIN",
        ProposedChange("UPDATE_FIELD", "mem-a2", fields={"membership_status": "SUSPENDED"}),
        SELF_ACTOR,
        FULL_EVIDENCE,
    ),
]


def run_case(case: Case) -> CorrectionSimulation:
    return simulate_correction(HOUSEHOLD, case.proposed, case.actor, evidence=case.evidence)


def run_evaluation() -> dict[str, Any]:
    results = []
    for case in CASES:
        simulation = run_case(case)
        results.append(
            {
                "key": case.key,
                "label": case.label,
                "expected": case.expected,
                "risk_level": simulation.risk_level,
                "blocked": simulation.blocked,
                "requires_review": simulation.requires_review,
                "safe_to_submit": simulation.safe_to_submit,
                "caught_before_submission": simulation.blocked or simulation.requires_review or not simulation.safe_to_submit,
                "findings": [finding["code"] for finding in simulation.findings],
            }
        )

    harmful = [r for r in results if r["expected"] == "HARMFUL"]
    harmless = [r for r in results if r["expected"] == "HARMLESS"]
    uncertain = [r for r in results if r["expected"] == "UNCERTAIN"]

    caught = [r for r in harmful if r["caught_before_submission"]]
    false_positives = [r for r in harmless if r["caught_before_submission"]]
    uncertain_flagged = [r for r in uncertain if r["caught_before_submission"]]

    harmful_recall = len(caught) / len(harmful) if harmful else 0.0
    return {
        "dataset": "synthetic seeded correction cases",
        "is_synthetic": True,
        "case_count": len(results),
        "results": results,
        "harmful_detection": {
            "total": len(harmful),
            "caught": len(caught),
            "recall": harmful_recall,
            "uncaught": [r["key"] for r in harmful if not r["caught_before_submission"]],
            "target": 1.0,
            "caveat": "This finite synthetic set does not prove universal real-world protection.",
        },
        "false_positives": {
            "total": len(harmless),
            "count": len(false_positives),
            "rate": len(false_positives) / len(harmless) if harmless else 0.0,
            "cases": [r["key"] for r in false_positives],
        },
        "uncertain_cases": {
            "total": len(uncertain),
            "flagged_for_review": len(uncertain_flagged),
            "rate": len(uncertain_flagged) / len(uncertain) if uncertain else 0.0,
            "cases": [r["key"] for r in uncertain_flagged],
        },
        "blocked_cases": [r["key"] for r in results if r["risk_level"] == RiskLevel.BLOCKED],
        "notes": [
            "Risk labels are operational, not legal determinations.",
            "A warning alone is not used for entitlement-removing changes; those are BLOCKED.",
        ],
    }
