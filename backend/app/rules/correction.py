"""Safe record-correction simulator (pure, deterministic).

The simulator compares the existing synthetic household record with a proposed
correction and returns risk findings *before* any submission path is available.

Hard rule: a proposal that removes a member, an entitlement link, or a draw
history link is BLOCKED. A warning is not sufficient, and the caller cannot
override the block. Uncertain situations are REVIEW_REQUIRED, which also
prevents automated submission.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.domain import RISK_ORDER, CorrectionOperation, RiskLevel


@dataclass(frozen=True)
class EntitlementFact:
    id: str
    commodity_code: str
    period: str
    entitled_qty: float | None
    drawn_qty: float | None
    remaining_qty: float | None
    provenance: str


@dataclass(frozen=True)
class MemberFact:
    id: str
    alias: str
    name: str
    age: int | None
    membership_status: str
    is_head: bool = False
    is_dependent: bool = False
    document_name: str | None = None
    document_age: int | None = None
    document_ref: str | None = None
    entitlements: tuple[EntitlementFact, ...] = ()


@dataclass(frozen=True)
class HouseholdFact:
    id: str
    reference: str
    members: tuple[MemberFact, ...]


@dataclass(frozen=True)
class ProposedChange:
    operation: str
    member_id: str
    fields: dict[str, Any] = field(default_factory=dict)
    new_member: dict[str, Any] | None = None
    merge_into_member_id: str | None = None
    reason: str | None = None


@dataclass(frozen=True)
class ActorContext:
    role: str
    session_member_id: str | None
    can_change_identity: bool = False
    can_change_membership: bool = False
    consent_recorded: bool = False
    head_absent: bool = False


@dataclass
class CorrectionSimulation:
    risk_level: str
    blocked: bool
    requires_review: bool
    safe_to_submit: bool
    findings: list[dict[str, Any]]
    before: dict[str, Any]
    after: dict[str, Any]
    diff: dict[str, Any]
    evidence_checklist: list[dict[str, Any]]
    summary: list[str]
    recommended_action: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "risk_level": self.risk_level,
            "blocked": self.blocked,
            "requires_review": self.requires_review,
            "safe_to_submit": self.safe_to_submit,
            "findings": self.findings,
            "before": self.before,
            "after": self.after,
            "diff": self.diff,
            "evidence_checklist": self.evidence_checklist,
            "summary": self.summary,
            "recommended_action": self.recommended_action,
        }


IDENTITY_FIELDS = {"name", "age", "document_name", "document_age", "document_ref"}
MEMBERSHIP_FIELDS = {"membership_status", "is_head", "is_dependent"}
ALLOWED_FIELDS = IDENTITY_FIELDS | MEMBERSHIP_FIELDS


def _find(fact: HouseholdFact, member_id: str | None) -> MemberFact | None:
    return next((m for m in fact.members if m.id == member_id), None)


def _normalise(value: str) -> str:
    return " ".join(value.casefold().split())


def levenshtein(a: str, b: str) -> int:
    a, b = _normalise(a), _normalise(b)
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        current = [i]
        for j, cb in enumerate(b, 1):
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (ca != cb)))
        previous = current
    return previous[-1]


def _member_state(member: MemberFact) -> dict[str, Any]:
    return {
        "member_id": member.id,
        "alias": member.alias,
        "name": member.name,
        "age": member.age,
        "membership_status": member.membership_status,
        "is_head": member.is_head,
        "is_dependent": member.is_dependent,
        "document_name": member.document_name,
        "document_age": member.document_age,
        "document_ref_present": bool(member.document_ref),
        "entitlement_links": [
            {
                "id": e.id,
                "commodity": e.commodity_code,
                "period": e.period,
                "entitled_qty": e.entitled_qty,
                "drawn_qty": e.drawn_qty,
                "remaining_qty": e.remaining_qty,
                "provenance": e.provenance,
            }
            for e in member.entitlements
        ],
    }


def _household_state(fact: HouseholdFact, members: list[MemberFact]) -> dict[str, Any]:
    return {
        "household_ref": fact.reference,
        "member_count": len(members),
        "members": [_member_state(m) for m in members],
        "entitlement_link_count": sum(len(m.entitlements) for m in members),
    }


def _evidence_item(item_id: str, label: str, required: bool, provided: list[str]) -> dict[str, Any]:
    return {"id": item_id, "label": label, "required": required, "provided": item_id in provided}


def _replace_member(house: HouseholdFact, updated: MemberFact) -> list[MemberFact]:
    return [updated if m.id == updated.id else m for m in house.members]


def simulate_correction(
    house: HouseholdFact,
    proposed: ProposedChange,
    actor: ActorContext,
    evidence: list[str] | None = None,
    rules_version: str = "synthetic-2026.1",
) -> CorrectionSimulation:
    evidence = list(evidence or [])
    findings: list[dict[str, Any]] = []
    summary: list[str] = []

    def add(code: str, severity: str, message: str, *, blocking: bool = False, member_ref: str | None = None,
            entitlement_ref: str | None = None) -> None:
        findings.append(
            {
                "code": code,
                "severity": severity,
                "message": message,
                "blocking": blocking,
                "member_ref": member_ref,
                "entitlement_ref": entitlement_ref,
            }
        )

    target = _find(house, proposed.member_id)
    before = _household_state(house, list(house.members))
    members_after: list[MemberFact] = list(house.members)
    operation = proposed.operation

    # ---- authority checks (defence in depth; API also enforces) ----------
    is_target = actor.session_member_id == proposed.member_id
    if proposed.member_id is None or target is None:
        add("member_not_found", RiskLevel.BLOCKED, "The selected member does not exist in this household record.", blocking=True)
        members_after = list(house.members)
    elif operation in {CorrectionOperation.UPDATE_FIELD, CorrectionOperation.DELETE_MEMBER, CorrectionOperation.REPLACE_MEMBER, CorrectionOperation.MERGE_DUPLICATE}:
        # Self-service only in this prototype. Acting for another adult requires an
        # authorised-representative record, which is not granted by any demo session.
        authorised = is_target and actor.can_change_identity
        if not authorised:
            add(
                "unauthorised_edit",
                RiskLevel.BLOCKED,
                "This session is not authorised to change another member's record. Nothing was changed.",
                blocking=True,
                member_ref=proposed.member_id,
            )
        if actor.role == "FACILITATOR":
            add(
                "facilitator_cannot_edit_identity",
                RiskLevel.BLOCKED,
                "A facilitator session can prepare a draft but cannot edit identity-linked fields for another adult.",
                blocking=True,
                member_ref=proposed.member_id,
            )

    # ---- operation application -------------------------------------------
    if target is not None and not findings:
        if operation == CorrectionOperation.UPDATE_FIELD:
            unknown = sorted(set(proposed.fields) - ALLOWED_FIELDS)
            if unknown:
                add(
                    "unsupported_field",
                    RiskLevel.REVIEW_REQUIRED,
                    "Only name, age, membership and synthetic document fields can be simulated here: " + ", ".join(unknown),
                    member_ref=proposed.member_id,
                )
            if "membership_status" in proposed.fields and not actor.can_change_membership:
                add(
                    "membership_authority_unverified",
                    RiskLevel.REVIEW_REQUIRED,
                    "A membership-status change requires household authority and authorised human review.",
                    member_ref=proposed.member_id,
                )
            updates = {k: v for k, v in proposed.fields.items() if k in ALLOWED_FIELDS}
            if not updates:
                add("no_supported_change", RiskLevel.REVIEW_REQUIRED, "No supported change was proposed.")
            updated = MemberFact(
                id=target.id,
                alias=target.alias,
                name=str(updates.get("name", target.name)),
                age=_coerce_age(updates.get("age", target.age)),
                membership_status=str(updates.get("membership_status", target.membership_status)),
                is_head=bool(updates.get("is_head", target.is_head)),
                is_dependent=bool(updates.get("is_dependent", target.is_dependent)),
                document_name=updates.get("document_name", target.document_name),
                document_age=_coerce_age(updates.get("document_age", target.document_age)),
                document_ref=updates.get("document_ref", target.document_ref),
                entitlements=target.entitlements,
            )
            if updated.membership_status in {"REMOVED", "DELETED", "INACTIVE"} and target.membership_status not in {"REMOVED", "DELETED", "INACTIVE"}:
                add(
                    "membership_removal",
                    RiskLevel.BLOCKED,
                    "Marking a member inactive/removed through a correction is a destructive membership change. Use reconciliation with authorised review.",
                    blocking=True,
                    member_ref=target.id,
                )
            if updated.name != target.name:
                _classify_name_change(target, updated, evidence, add)
            if updated.age != target.age:
                _classify_age_change(target, updated, evidence, add)
            if (
                "age" in updates
                and updated.document_age is not None
                and updated.age is not None
                and updated.document_age != updated.age
            ):
                add(
                    "identity_document_conflict",
                    RiskLevel.REVIEW_REQUIRED,
                    "The proposed age still conflicts with the synthetic identity-document age; the correct value is uncertain.",
                    member_ref=target.id,
                )
            members_after = _replace_member(house, updated)

        elif operation == CorrectionOperation.DELETE_MEMBER:
            add(
                "member_removal_blocked",
                RiskLevel.BLOCKED,
                "Deleting a household member is blocked. Deletion can silently remove entitlement and draw history.",
                blocking=True,
                member_ref=target.id,
            )
            if target.entitlements:
                add(
                    "entitlement_link_removal",
                    RiskLevel.BLOCKED,
                    f"Deletion would remove {len(target.entitlements)} entitlement link(s) for this member.",
                    blocking=True,
                    member_ref=target.id,
                    entitlement_ref=target.entitlements[0].id,
                )
            if any((e.drawn_qty or 0) > 0 for e in target.entitlements):
                add(
                    "draw_history_affected",
                    RiskLevel.BLOCKED,
                    "Deletion would break links to recorded draw history for this member.",
                    blocking=True,
                    member_ref=target.id,
                )
            members_after = [m for m in house.members if m.id != target.id]

        elif operation == CorrectionOperation.REPLACE_MEMBER:
            add(
                "replace_member_blocked",
                RiskLevel.BLOCKED,
                "Replacing a member deletes the original record. Reconciliation is safer than delete-and-recreate.",
                blocking=True,
                member_ref=target.id,
            )
            if target.entitlements:
                add(
                    "entitlement_link_removal",
                    RiskLevel.BLOCKED,
                    "The replacement would drop the member's existing entitlement links.",
                    blocking=True,
                    member_ref=target.id,
                )
            members_after = [m for m in house.members if m.id != target.id]

        elif operation == CorrectionOperation.CREATE_MEMBER:
            new_member = proposed.new_member or {}
            name = str(new_member.get("name", "")).strip()
            age = _coerce_age(new_member.get("age"))
            if not name:
                add("missing_new_member_name", RiskLevel.BLOCKED, "A new member needs a name.", blocking=True)
            duplicate = next(
                (
                    m
                    for m in house.members
                    if _normalise(m.name) == _normalise(name)
                    or (m.document_name is not None and _normalise(m.document_name) == _normalise(name))
                    or (
                        age is not None
                        and (
                            (m.age is not None and m.age == age)
                            or (m.document_age is not None and m.document_age == age)
                        )
                        and (levenshtein(m.name, name) <= 2 or (
                            m.document_name is not None and levenshtein(m.document_name, name) <= 2
                        ))
                    )
                ),
                None,
            )
            if duplicate is not None:
                add(
                    "possible_duplicate_member",
                    RiskLevel.HIGH,
                    "A member with a very similar name and age already exists. Creating another record may split one person into two records.",
                    member_ref=duplicate.id,
                )
                add(
                    "duplicate_requires_review",
                    RiskLevel.REVIEW_REQUIRED,
                    "Confirm the existing member's identity before creating a new record.",
                    member_ref=duplicate.id,
                )
            add(
                "new_member_requires_verification",
                RiskLevel.REVIEW_REQUIRED,
                "A new member record needs authorised verification before any entitlement is attached.",
            )
            members_after = list(house.members)

        elif operation == CorrectionOperation.MERGE_DUPLICATE:
            other = _find(house, proposed.merge_into_member_id)
            if other is None:
                add("merge_target_missing", RiskLevel.BLOCKED, "The merge target does not exist.", blocking=True)
            else:
                add(
                    "merge_requires_review",
                    RiskLevel.REVIEW_REQUIRED,
                    "Merging would combine two member records. Entitlement and draw-history links need authorised reconciliation.",
                    member_ref=target.id,
                )
                members_after = [m for m in house.members if m.id != target.id]
        else:
            add("unknown_operation", RiskLevel.BLOCKED, "This operation is not supported.", blocking=True)
    elif proposed.member_id is not None and target is None:
        members_after = list(house.members)

    # ---- generic evidence checks ------------------------------------------
    identity_change = operation == CorrectionOperation.UPDATE_FIELD and bool(set(proposed.fields) & IDENTITY_FIELDS)
    checklist = _build_checklist(operation, identity_change, bool(proposed.fields.get("membership_status")), evidence)
    missing = [item for item in checklist if item["required"] and not item["provided"]]
    for item in missing:
        add(
            "evidence_missing",
            RiskLevel.REVIEW_REQUIRED,
            f"Required supporting evidence is missing: {item['label']}.",
        )
    if identity_change and not any(f["severity"] == RiskLevel.BLOCKED for f in findings):
        add(
            "provenance_not_upgraded",
            RiskLevel.LOW,
            "Existing provenance is preserved; the proposal will not be treated as an official record.",
        )

    # ---- diff --------------------------------------------------------------
    before_ids = {m.id for m in house.members}
    after_ids = {m.id for m in members_after}
    removed_ids = sorted(before_ids - after_ids)
    added_ids = sorted(after_ids - before_ids)
    modified_ids = sorted(
        m.id
        for m in members_after
        if m.id in before_ids and _member_state(m) != _member_state(_find(house, m.id))  # type: ignore[arg-type]
    )
    before_links = {e.id: e for m in house.members for e in m.entitlements}
    after_links = {e.id: e for m in members_after for e in m.entitlements}
    lost_links = sorted(set(before_links) - set(after_links))
    affected_periods = sorted({before_links[i].period for i in lost_links})
    draw_links_affected = sorted(i for i in lost_links if (before_links[i].drawn_qty or 0) > 0)

    # Any entitlement disappearance is destructive regardless of operation.
    if lost_links and not any(f["code"] in {"entitlement_link_removal", "member_removal_blocked"} for f in findings):
        add(
            "entitlement_link_removal",
            RiskLevel.BLOCKED,
            f"The proposed change would remove {len(lost_links)} entitlement link(s) from the simulated record.",
            blocking=True,
        )

    after = _household_state(house, members_after)
    diff = {
        "members_added": added_ids,
        "members_removed": removed_ids,
        "members_modified": modified_ids,
        "member_count_before": len(house.members),
        "member_count_after": len(members_after),
        "entitlement_links_before": len(before_links),
        "entitlement_links_after": len(after_links),
        "entitlement_links_removed": lost_links,
        "entitlement_periods_affected": affected_periods,
        "draw_history_links_affected": draw_links_affected,
        "unresolved_identity_conflicts": [f["message"] for f in findings if f["code"] in {
            "name_mismatch", "age_mismatch", "identity_document_conflict", "possible_duplicate_member", "multiple_conflicts"
        }],
    }

    # ---- aggregate classification ------------------------------------------
    blocking = any(f["blocking"] or f["severity"] == RiskLevel.BLOCKED for f in findings)
    severities = {f["severity"] for f in findings}
    if blocking:
        risk = RiskLevel.BLOCKED
    elif RiskLevel.HIGH in severities:
        risk = RiskLevel.HIGH
    elif RiskLevel.REVIEW_REQUIRED in severities:
        risk = RiskLevel.REVIEW_REQUIRED
    else:
        risk = RiskLevel.LOW

    requires_review = risk in {RiskLevel.REVIEW_REQUIRED, RiskLevel.HIGH, RiskLevel.BLOCKED}
    safe_to_submit = risk == RiskLevel.LOW and not blocking

    if removed_ids:
        summary.append(
            f"The proposal would reduce the household from {len(house.members)} to {len(members_after)} member(s)."
        )
    elif operation == CorrectionOperation.CREATE_MEMBER:
        summary.append(
            f"The proposal would increase the household from {len(house.members)} to {len(members_after)} member(s)."
        )
    else:
        summary.append("The proposal does not change the number of household members in the simulated record.")
    summary.append("No official record has been changed by this simulation.")
    if lost_links:
        summary.append(f"{len(lost_links)} entitlement link(s) would disappear from the simulated record.")

    if blocking:
        action = "Stop. Preserve the original record and ask an authorised office to reconcile the mismatch."
    elif requires_review:
        action = "Pause submission, collect the missing evidence, and seek authorised human review."
    else:
        action = "Save this as a draft. Submission is only possible through the labelled demo adapter and is not an official filing."
    summary.append(action)

    findings.sort(key=lambda f: RISK_ORDER[RiskLevel(f["severity"])], reverse=True)

    return CorrectionSimulation(
        risk_level=str(risk),
        blocked=blocking,
        requires_review=requires_review,
        safe_to_submit=safe_to_submit,
        findings=findings,
        before=before,
        after=after,
        diff=diff,
        evidence_checklist=checklist,
        summary=summary,
        recommended_action=action,
    )


def _coerce_age(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _classify_name_change(target: MemberFact, updated: MemberFact, evidence: list[str], add) -> None:  # type: ignore[no-untyped-def]
    distance = levenshtein(target.name, updated.name)
    if distance <= 2 and target.name[:1].casefold() == updated.name[:1].casefold():
        add(
            "spelling_variation",
            RiskLevel.LOW,
            "This looks like a spelling variation of the same name; the member record is preserved.",
            member_ref=target.id,
        )
        if "identity_reference" not in evidence:
            add(
                "evidence_missing_name",
                RiskLevel.REVIEW_REQUIRED,
                "Attach the synthetic identity reference before relying on a spelling correction.",
                member_ref=target.id,
            )
    else:
        add(
            "name_mismatch",
            RiskLevel.REVIEW_REQUIRED,
            "The proposed name is substantially different from the household record. The correct value needs verification.",
            member_ref=target.id,
        )


def _classify_age_change(target: MemberFact, updated: MemberFact, evidence: list[str], add) -> None:  # type: ignore[no-untyped-def]
    if updated.age is None:
        add("invalid_age", RiskLevel.REVIEW_REQUIRED, "The proposed age is missing or invalid.", member_ref=target.id)
        return
    if updated.age < 0 or updated.age > 120:
        add("implausible_age", RiskLevel.HIGH, "The proposed age is outside a plausible range.", member_ref=target.id)
        return
    delta = abs(updated.age - (target.age or updated.age))
    if delta <= 2 and updated.document_age == updated.age:
        add(
            "age_correction_supported",
            RiskLevel.LOW,
            "The synthetic identity document supports the proposed age; all membership and entitlement links are preserved.",
            member_ref=target.id,
        )
    elif updated.document_age == updated.age:
        add(
            "age_correction_large",
            RiskLevel.REVIEW_REQUIRED,
            "The proposed age differs substantially from the household record even though the document matches. Review is required.",
            member_ref=target.id,
        )
    else:
        add(
            "age_mismatch",
            RiskLevel.REVIEW_REQUIRED,
            "The proposed age is not fully supported by the available document values; review is required.",
            member_ref=target.id,
        )
        if updated.document_age is not None and updated.document_age != updated.age:
            add(
                "conflicting_evidence",
                RiskLevel.REVIEW_REQUIRED,
                "Evidence conflicts: the document age, proposed age and household age disagree.",
                member_ref=target.id,
            )


def _build_checklist(operation: str, identity_change: bool, membership_change: bool, provided: list[str]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    if operation in {CorrectionOperation.UPDATE_FIELD, CorrectionOperation.CREATE_MEMBER, CorrectionOperation.MERGE_DUPLICATE}:
        items.append(_evidence_item("identity_reference", "Synthetic identity reference (demo)", True, provided))
    if identity_change or operation in {CorrectionOperation.CREATE_MEMBER, CorrectionOperation.MERGE_DUPLICATE}:
        items.append(_evidence_item("household_reference", "Synthetic household reference", True, provided))
    if membership_change:
        items.append(_evidence_item("household_authority", "Proof of authority for a membership change", True, provided))
    if operation in {CorrectionOperation.DELETE_MEMBER, CorrectionOperation.REPLACE_MEMBER}:
        items.append(_evidence_item("authorised_office_confirmation", "Authorised-office reconciliation note", True, provided))
    items.append(_evidence_item("member_confirmation", "Household member confirms the submitted values", True, provided))
    return items
