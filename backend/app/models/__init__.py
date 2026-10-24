"""Normalised persistence model for RationSaathi.

Design notes
------------
* Identifiers are internal UUID strings; no official identity numbers are stored.
* Every critical value carries provenance and verification status.
* Entitlements live per member AND per commodity (never a household total).
* Audit events are append-only and deliberately avoid sensitive values.
* No cascading deletes are configured: entitlement/draw history is never
  silently destroyed by removing a member.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship as orm_relationship

from app.db import Base, utcnow


def new_id() -> str:
    return str(uuid.uuid4())


class Household(Base):
    __tablename__ = "households"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    reference: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    home_state: Mapped[str] = mapped_column(String(80), nullable=False)
    home_jurisdiction_code: Mapped[str] = mapped_column(String(16), nullable=False)
    destination_state: Mapped[str] = mapped_column(String(80), nullable=False)
    destination_jurisdiction_code: Mapped[str] = mapped_column(String(16), nullable=False)
    destination_shop_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    provenance: Mapped[str] = mapped_column(String(40), default="SYNTHETIC_DEMO", nullable=False)
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    members: Mapped[list["Member"]] = orm_relationship(back_populates="household", lazy="selectin")


class Member(Base):
    __tablename__ = "household_members"
    __table_args__ = (Index("ix_members_household", "household_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    household_id: Mapped[str] = mapped_column(ForeignKey("households.id"), nullable=False)
    display_alias: Mapped[str] = mapped_column(String(80), nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    age_band: Mapped[str | None] = mapped_column(String(20), nullable=True)
    membership_status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False)
    relationship: Mapped[str | None] = mapped_column(String(40), nullable=True)
    verification_state: Mapped[str] = mapped_column(String(32), default="UNVERIFIED", nullable=False)
    provenance: Mapped[str] = mapped_column(String(40), default="SYNTHETIC_DEMO", nullable=False)
    consent_state: Mapped[str] = mapped_column(String(32), default="NOT_RECORDED", nullable=False)
    is_head: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_absent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_dependent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Synthetic identity-document reference/value pairs used for the mismatch demo.
    document_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    document_age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    document_ref: Mapped[str | None] = mapped_column(String(40), nullable=True)
    document_provenance: Mapped[str | None] = mapped_column(String(40), nullable=True)
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    household: Mapped[Household] = orm_relationship(back_populates="members")
    entitlements: Mapped[list["MemberEntitlement"]] = orm_relationship(
        back_populates="member", lazy="selectin", foreign_keys="MemberEntitlement.member_id"
    )


class MemberConsent(Base):
    __tablename__ = "member_consents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    member_id: Mapped[str] = mapped_column(ForeignKey("household_members.id"), nullable=False)
    scope: Mapped[str] = mapped_column(String(64), nullable=False)
    granted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    provenance: Mapped[str] = mapped_column(String(40), default="SYNTHETIC_DEMO", nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    recorded_by_session: Mapped[str | None] = mapped_column(String(36), nullable=True)


class UserSession(Base):
    __tablename__ = "user_sessions"
    __table_args__ = (Index("ix_sessions_household", "household_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    household_id: Mapped[str | None] = mapped_column(ForeignKey("households.id"), nullable=True)
    member_id: Mapped[str | None] = mapped_column(ForeignKey("household_members.id"), nullable=True)
    permissions: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    consent_member_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    facilitator_device: Mapped[str | None] = mapped_column(String(64), nullable=True)
    purpose: Mapped[str] = mapped_column(String(32), default="MEMBER_SELF_SERVICE", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_reason: Mapped[str | None] = mapped_column(String(40), nullable=True)
    cleanup_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Commodity(Base):
    __tablename__ = "commodities"

    code: Mapped[str] = mapped_column(String(24), primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class MemberEntitlement(Base):
    __tablename__ = "member_entitlements"
    __table_args__ = (
        UniqueConstraint("member_id", "commodity_code", "period", name="uq_entitlement_member_commodity_period"),
        Index("ix_entitlements_member", "member_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    member_id: Mapped[str] = mapped_column(ForeignKey("household_members.id"), nullable=False)
    commodity_code: Mapped[str] = mapped_column(ForeignKey("commodities.code"), nullable=False)
    period: Mapped[str] = mapped_column(String(16), nullable=False)
    entitled_qty: Mapped[float | None] = mapped_column(Float, nullable=True)
    drawn_qty: Mapped[float | None] = mapped_column(Float, nullable=True)
    remaining_qty: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    provenance: Mapped[str] = mapped_column(String(40), default="SYNTHETIC_DEMO", nullable=False)
    verification_status: Mapped[str] = mapped_column(String(32), default="UNVERIFIED", nullable=False)
    jurisdiction: Mapped[str] = mapped_column(String(16), nullable=False)
    rules_version: Mapped[str] = mapped_column(String(32), nullable=False)
    source_ref: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    member: Mapped[Member] = orm_relationship(back_populates="entitlements")


class RationShop(Base):
    __tablename__ = "ration_shops"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    jurisdiction_code: Mapped[str] = mapped_column(String(16), nullable=False)
    address_label: Mapped[str] = mapped_column(String(160), nullable=False)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class StockObservation(Base):
    __tablename__ = "stock_observations"
    __table_args__ = (Index("ix_stock_shop_commodity", "shop_id", "commodity_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    shop_id: Mapped[str] = mapped_column(ForeignKey("ration_shops.id"), nullable=False)
    commodity_code: Mapped[str] = mapped_column(ForeignKey("commodities.code"), nullable=False)
    state: Mapped[str] = mapped_column(String(40), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[str] = mapped_column(String(80), nullable=False)
    source_ref: Mapped[str | None] = mapped_column(String(64), nullable=True)
    provenance: Mapped[str] = mapped_column(String(40), default="SYNTHETIC_DEMO", nullable=False)
    note: Mapped[str | None] = mapped_column(String(240), nullable=True)


class RuleVersion(Base):
    __tablename__ = "rule_versions"
    __table_args__ = (UniqueConstraint("scope", "version", name="uq_rule_scope_version"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    scope: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_label: Mapped[str] = mapped_column(String(160), nullable=False)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class RecordSnapshot(Base):
    __tablename__ = "record_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    household_id: Mapped[str] = mapped_column(ForeignKey("households.id"), nullable=False)
    member_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    reason: Mapped[str] = mapped_column(String(80), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class CorrectionProposal(Base):
    __tablename__ = "correction_proposals"
    __table_args__ = (Index("ix_proposals_household", "household_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    household_id: Mapped[str] = mapped_column(ForeignKey("households.id"), nullable=False)
    member_id: Mapped[str] = mapped_column(String(36), nullable=False)
    operation: Mapped[str] = mapped_column(String(32), nullable=False)
    request_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(24), nullable=False)
    blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    before_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    after_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    findings: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    rule_version: Mapped[str] = mapped_column(String(32), nullable=False)
    created_by_session: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    submission_receipt: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)


class CorrectionRiskFindingRow(Base):
    __tablename__ = "correction_risk_findings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("correction_proposals.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(24), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    member_ref: Mapped[str | None] = mapped_column(String(36), nullable=True)
    entitlement_ref: Mapped[str | None] = mapped_column(String(36), nullable=True)
    blocking: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class EvidenceChecklist(Base):
    __tablename__ = "evidence_checklists"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("correction_proposals.id"), nullable=False)
    items: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class OfflineDraft(Base):
    __tablename__ = "offline_drafts"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_draft_idempotency"),
        UniqueConstraint("draft_ref", name="uq_draft_ref"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    draft_ref: Mapped[str] = mapped_column(String(24), nullable=False)
    household_id: Mapped[str] = mapped_column(ForeignKey("households.id"), nullable=False)
    member_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    kind: Mapped[str] = mapped_column(String(40), nullable=False)
    state: Mapped[str] = mapped_column(String(40), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(80), nullable=False)
    created_by_session: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    last_error: Mapped[str | None] = mapped_column(String(240), nullable=True)
    official_receipt_id: Mapped[str | None] = mapped_column(String(36), nullable=True)


class DraftVersion(Base):
    __tablename__ = "draft_versions"
    __table_args__ = (UniqueConstraint("draft_id", "version", name="uq_draft_version"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    draft_id: Mapped[str] = mapped_column(ForeignKey("offline_drafts.id"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class SubmissionAttempt(Base):
    __tablename__ = "submission_attempts"
    __table_args__ = (UniqueConstraint("idempotency_key", name="uq_attempt_idempotency"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    draft_id: Mapped[str] = mapped_column(ForeignKey("offline_drafts.id"), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(80), nullable=False)
    adapter: Mapped[str] = mapped_column(String(40), nullable=False)
    outcome: Mapped[str] = mapped_column(String(40), nullable=False)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    response: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class SubmissionReceipt(Base):
    __tablename__ = "submission_receipts"
    __table_args__ = (UniqueConstraint("receipt_number", name="uq_receipt_number"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    draft_id: Mapped[str] = mapped_column(ForeignKey("offline_drafts.id"), nullable=False)
    receipt_number: Mapped[str] = mapped_column(String(48), nullable=False)
    adapter: Mapped[str] = mapped_column(String(40), nullable=False)
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    raw: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class Grievance(Base):
    __tablename__ = "grievances"
    __table_args__ = (Index("ix_grievances_household", "household_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    household_id: Mapped[str] = mapped_column(ForeignKey("households.id"), nullable=False)
    member_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    category: Mapped[str] = mapped_column(String(48), nullable=False)
    subject: Mapped[str] = mapped_column(String(160), nullable=False)
    filed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    provenance: Mapped[str] = mapped_column(String(40), nullable=False)
    official_receipt_number: Mapped[str | None] = mapped_column(String(48), nullable=True)
    local_draft_ref: Mapped[str | None] = mapped_column(String(24), nullable=True)
    responsible_office: Mapped[str | None] = mapped_column(String(160), nullable=True)
    office_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    assigned_officer: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    last_status_update: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sla_policy_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    deadline_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    response_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolution_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    deadline_source_label: Mapped[str | None] = mapped_column(String(160), nullable=True)
    status_source: Mapped[str | None] = mapped_column(String(80), nullable=True)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class GrievanceEvent(Base):
    __tablename__ = "grievance_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    grievance_id: Mapped[str] = mapped_column(ForeignKey("grievances.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(48), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    detail: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class GrievanceAssignment(Base):
    __tablename__ = "grievance_assignments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    grievance_id: Mapped[str] = mapped_column(ForeignKey("grievances.id"), nullable=False)
    office: Mapped[str] = mapped_column(String(160), nullable=False)
    officer_placeholder: Mapped[str | None] = mapped_column(String(120), nullable=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class ServiceLevelPolicy(Base):
    __tablename__ = "service_level_policies"
    __table_args__ = (UniqueConstraint("category", "jurisdiction_code", "version", name="uq_sla_scope"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    category: Mapped[str] = mapped_column(String(48), nullable=False)
    jurisdiction_code: Mapped[str] = mapped_column(String(16), nullable=False)
    days: Mapped[int] = mapped_column(Integer, nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    source_label: Mapped[str] = mapped_column(String(200), nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class EscalationDraft(Base):
    __tablename__ = "escalation_drafts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    grievance_id: Mapped[str] = mapped_column(ForeignKey("grievances.id"), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    state: Mapped[str] = mapped_column(String(32), default="DRAFT_NOT_SUBMITTED", nullable=False)
    created_by_session: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    submitted_receipt: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)


class AuditEvent(Base):
    __tablename__ = "audit_events"
    __table_args__ = (Index("ix_audit_action", "action"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_role: Mapped[str | None] = mapped_column(String(20), nullable=True)
    session_ref: Mapped[str | None] = mapped_column(String(16), nullable=True)
    household_ref: Mapped[str | None] = mapped_column(String(32), nullable=True)
    member_ref: Mapped[str | None] = mapped_column(String(36), nullable=True)
    entity_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    outcome: Mapped[str] = mapped_column(String(24), default="OK", nullable=False)
    detail: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class AggregateMetric(Base):
    __tablename__ = "aggregate_metrics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    metric_key: Mapped[str] = mapped_column(String(64), nullable=False)
    jurisdiction_code: Mapped[str] = mapped_column(String(16), nullable=True)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False)
    window_label: Mapped[str] = mapped_column(String(32), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    suppressed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
