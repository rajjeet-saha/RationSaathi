"""API schemas (Pydantic v2)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class SessionCreateRequest(BaseModel):
    household_id: str
    role: Literal["MEMBER", "FACILITATOR"] = "MEMBER"
    member_id: str | None = None
    purpose: Literal["MEMBER_SELF_SERVICE", "ASSISTED_SERVICE", "FACILITATOR_HANDOVER"] = "MEMBER_SELF_SERVICE"
    facilitator_device: str | None = None

    @field_validator("facilitator_device")
    @classmethod
    def _trim_device(cls, value: str | None) -> str | None:
        return value.strip()[:64] if value else None


class ConfirmConsentRequest(BaseModel):
    member_id: str
    consent_explained: bool = Field(default=False)
    consent_given: bool = Field(default=False)


class SessionSwitchRequest(BaseModel):
    member_id: str


class SessionEndRequest(BaseModel):
    reason: Literal["USER_LOGOUT", "FACILITATOR_HANDOVER", "TIMEOUT", "ERROR_RECOVERY", "ADMIN"] = "USER_LOGOUT"
    client_cleanup_confirmed: bool = False


class PortabilityEvaluateRequest(BaseModel):
    member_id: str
    commodity_code: str


class CorrectionSimulateRequest(BaseModel):
    operation: Literal["UPDATE_FIELD", "DELETE_MEMBER", "CREATE_MEMBER", "REPLACE_MEMBER", "MERGE_DUPLICATE"]
    member_id: str
    fields: dict[str, Any] = Field(default_factory=dict)
    new_member: dict[str, Any] | None = None
    merge_into_member_id: str | None = None
    evidence: list[str] = Field(default_factory=list)
    reason: str | None = Field(default=None, max_length=500)


class CorrectionDraftRequest(BaseModel):
    evidence: list[str] = Field(default_factory=list)
    note: str | None = Field(default=None, max_length=500)


class DraftCreateRequest(BaseModel):
    kind: Literal["CORRECTION", "GRIEVANCE", "PORTABILITY_REQUEST", "ASSISTED_FORM"]
    member_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = Field(default=None, max_length=80)


class DraftUpdateRequest(BaseModel):
    payload: dict[str, Any]
    expected_version: int


class DraftSyncRequest(BaseModel):
    network_online: bool = True


class DraftVerifyRequest(BaseModel):
    simulate_receipt: bool = False


class EscalationDraftRequest(BaseModel):
    recipient_office: str | None = Field(default=None, max_length=160)
    officer_placeholder: str | None = Field(default=None, max_length=120)
    safe_contact: str | None = Field(default=None, max_length=160)
    body: str | None = Field(default=None, max_length=8000)


class EscalationUpdateRequest(BaseModel):
    body: str = Field(min_length=1, max_length=8000)


class EscalationSubmitRequest(BaseModel):
    confirm_authorised_channel: bool = False


class DemoResetRequest(BaseModel):
    confirm: bool = True


class HealthResponse(BaseModel):
    status: str
    demo_mode: bool
    rules_version: str
    database: str
    simulated_submission: bool
    generated_at: datetime
