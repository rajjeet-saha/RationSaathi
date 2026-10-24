"""Shared domain vocabulary: provenance, risk, draft and grievance states.

These labels are the single source of truth used by the database, rules engine,
APIs and the frontend mirrors.
"""

from __future__ import annotations

from enum import StrEnum


class Provenance(StrEnum):
    OFFICIAL_VERIFIED = "OFFICIAL_VERIFIED"
    OFFICIAL_LAST_SYNCED = "OFFICIAL_LAST_SYNCED"
    HOUSEHOLD_REPORTED = "HOUSEHOLD_REPORTED"
    FACILITATOR_ENTERED = "FACILITATOR_ENTERED"
    SYNTHETIC_DEMO = "SYNTHETIC_DEMO"
    UNKNOWN = "UNKNOWN"


PROVENANCE_LABELS: dict[str, str] = {
    Provenance.OFFICIAL_VERIFIED: "Official — verified",
    Provenance.OFFICIAL_LAST_SYNCED: "Official — last synced",
    Provenance.HOUSEHOLD_REPORTED: "Reported by household",
    Provenance.FACILITATOR_ENTERED: "Entered by facilitator",
    Provenance.SYNTHETIC_DEMO: "Synthetic demo data",
    Provenance.UNKNOWN: "Source unknown",
}


class StockState(StrEnum):
    AVAILABLE_VERIFIED = "AVAILABLE_VERIFIED"
    REPORTED_AVAILABLE = "REPORTED_AVAILABLE"
    OUT_OF_STOCK_REPORTED = "OUT_OF_STOCK_REPORTED"
    OUT_OF_STOCK_VERIFIED = "OUT_OF_STOCK_VERIFIED"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"


STOCK_STATE_LABELS: dict[str, str] = {
    StockState.AVAILABLE_VERIFIED: "Available — verified",
    StockState.REPORTED_AVAILABLE: "Reported available (not verified)",
    StockState.OUT_OF_STOCK_REPORTED: "Reported out of stock",
    StockState.OUT_OF_STOCK_VERIFIED: "Out of stock — verified",
    StockState.STALE: "Stock report is stale",
    StockState.UNKNOWN: "Stock unknown",
    StockState.SOURCE_UNAVAILABLE: "Stock source unavailable",
}


class Decision(StrEnum):
    ELIGIBLE = "ELIGIBLE_TO_PROCEED"
    POTENTIALLY_ELIGIBLE = "POTENTIALLY_ELIGIBLE_VERIFICATION_REQUIRED"
    MORE_INFORMATION = "MORE_INFORMATION_REQUIRED"
    NOT_SUPPORTED = "NOT_SUPPORTED_BY_CONFIGURED_RULES"
    CANNOT_DETERMINE = "CANNOT_DETERMINE_FROM_AVAILABLE_DATA"


class RiskLevel(StrEnum):
    LOW = "LOW"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    HIGH = "HIGH"
    BLOCKED = "BLOCKED"


RISK_ORDER = {RiskLevel.LOW: 0, RiskLevel.REVIEW_REQUIRED: 1, RiskLevel.HIGH: 2, RiskLevel.BLOCKED: 3}


class ProposalStatus(StrEnum):
    SIMULATED = "SIMULATED"
    SAVED_DRAFT = "SAVED_DRAFT"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    BLOCKED = "BLOCKED"
    SUBMISSION_PENDING = "SUBMISSION_PENDING"
    SUBMITTED_CONFIRMED = "SUBMITTED_CONFIRMED"


class CorrectionOperation(StrEnum):
    UPDATE_FIELD = "UPDATE_FIELD"
    DELETE_MEMBER = "DELETE_MEMBER"
    CREATE_MEMBER = "CREATE_MEMBER"
    REPLACE_MEMBER = "REPLACE_MEMBER"
    MERGE_DUPLICATE = "MERGE_DUPLICATE"


class DraftState(StrEnum):
    DRAFT_NOT_SUBMITTED = "DRAFT_NOT_SUBMITTED"
    QUEUED_FOR_SYNC = "QUEUED_FOR_SYNC"
    SYNC_IN_PROGRESS = "SYNC_IN_PROGRESS"
    SUBMISSION_PENDING_VERIFICATION = "SUBMISSION_PENDING_VERIFICATION"
    SUBMITTED_CONFIRMED = "SUBMITTED_CONFIRMED"
    SUBMISSION_FAILED = "SUBMISSION_FAILED"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"
    CANCELLED = "CANCELLED"


DRAFT_STATE_LABELS: dict[str, str] = {
    DraftState.DRAFT_NOT_SUBMITTED: "Saved on this device — not submitted",
    DraftState.QUEUED_FOR_SYNC: "Waiting for a connection",
    DraftState.SYNC_IN_PROGRESS: "Syncing draft data — official submission not confirmed",
    DraftState.SUBMISSION_PENDING_VERIFICATION: "Submission response received; verifying receipt",
    DraftState.SUBMITTED_CONFIRMED: "Official submission confirmed",
    DraftState.SUBMISSION_FAILED: "Submission failed — your draft has not been confirmed as submitted",
    DraftState.REQUIRES_REVIEW: "Needs review before it can be sent",
    DraftState.CANCELLED: "Cancelled",
}

DRAFT_TRANSITIONS: dict[str, set[str]] = {
    DraftState.DRAFT_NOT_SUBMITTED: {DraftState.QUEUED_FOR_SYNC, DraftState.CANCELLED, DraftState.REQUIRES_REVIEW},
    DraftState.QUEUED_FOR_SYNC: {
        DraftState.SYNC_IN_PROGRESS,
        DraftState.DRAFT_NOT_SUBMITTED,
        DraftState.SUBMISSION_FAILED,
        DraftState.CANCELLED,
    },
    DraftState.SYNC_IN_PROGRESS: {
        DraftState.SUBMISSION_PENDING_VERIFICATION,
        DraftState.SUBMISSION_FAILED,
        DraftState.QUEUED_FOR_SYNC,
    },
    DraftState.SUBMISSION_PENDING_VERIFICATION: {
        DraftState.SUBMITTED_CONFIRMED,
        DraftState.SUBMISSION_FAILED,
        DraftState.REQUIRES_REVIEW,
    },
    DraftState.SUBMISSION_FAILED: {DraftState.QUEUED_FOR_SYNC, DraftState.CANCELLED},
    DraftState.REQUIRES_REVIEW: {DraftState.DRAFT_NOT_SUBMITTED, DraftState.CANCELLED},
    DraftState.SUBMITTED_CONFIRMED: set(),
    DraftState.CANCELLED: set(),
}


class GrievanceStatus(StrEnum):
    DRAFT = "DRAFT"
    FILED = "FILED"
    ASSIGNED = "ASSIGNED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    IN_REVIEW = "IN_REVIEW"
    INFORMATION_REQUESTED = "INFORMATION_REQUESTED"
    OVERDUE = "OVERDUE"
    ESCALATION_DRAFT = "ESCALATION_DRAFT"
    ESCALATED = "ESCALATED"
    RESOLVED = "RESOLVED"
    REOPENED = "REOPENED"
    STATUS_UNKNOWN = "STATUS_UNKNOWN"


class SessionRole(StrEnum):
    MEMBER = "MEMBER"
    FACILITATOR = "FACILITATOR"
    ADMIN = "ADMIN"
    PUBLIC = "PUBLIC"


class Permission(StrEnum):
    VIEW_OWN_PROFILE = "view_own_profile"
    VIEW_MEMBER_PROFILE = "view_member_profile"
    REQUEST_OWN_SERVICE = "request_own_service"
    ACT_FOR_DEPENDENT = "act_for_dependent"
    REQUEST_HOUSEHOLD_CHANGE = "request_household_change"
    CHANGE_MEMBERSHIP = "change_membership"
    CHANGE_IDENTITY_FIELDS = "change_identity_fields"
    SUBMIT_OFFICIAL_APPLICATION = "submit_official_application"
    GIVE_CONSENT_FOR_OTHER = "give_consent_for_other"
    VIEW_GRIEVANCE = "view_grievance"
    CREATE_ESCALATION = "create_escalation"
    FACILITATOR_ASSIST = "facilitator_assist"
    VIEW_AGGREGATES = "view_aggregates"
    REVIEW_CORRECTIONS = "review_corrections"


ROLE_PERMISSIONS: dict[str, tuple[str, ...]] = {
    SessionRole.MEMBER: (
        Permission.VIEW_OWN_PROFILE,
        Permission.VIEW_MEMBER_PROFILE,
        Permission.REQUEST_OWN_SERVICE,
        Permission.CHANGE_IDENTITY_FIELDS,
        Permission.SUBMIT_OFFICIAL_APPLICATION,
        Permission.VIEW_GRIEVANCE,
        Permission.CREATE_ESCALATION,
        Permission.VIEW_AGGREGATES,
    ),
    SessionRole.FACILITATOR: (
        Permission.FACILITATOR_ASSIST,
        Permission.VIEW_OWN_PROFILE,
        Permission.VIEW_MEMBER_PROFILE,
        Permission.VIEW_GRIEVANCE,
        Permission.CREATE_ESCALATION,
        Permission.VIEW_AGGREGATES,
        Permission.SUBMIT_OFFICIAL_APPLICATION,
    ),
    SessionRole.ADMIN: (
        Permission.VIEW_AGGREGATES,
        Permission.REVIEW_CORRECTIONS,
    ),
    SessionRole.PUBLIC: (Permission.VIEW_AGGREGATES,),
}
