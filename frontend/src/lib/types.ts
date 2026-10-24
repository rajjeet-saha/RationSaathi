// API response types shared by the frontend. Mirrors the FastAPI payloads.

export type Provenance =
  | "OFFICIAL_VERIFIED"
  | "OFFICIAL_LAST_SYNCED"
  | "HOUSEHOLD_REPORTED"
  | "FACILITATOR_ENTERED"
  | "SYNTHETIC_DEMO"
  | "UNKNOWN";

export type RiskLevel = "LOW" | "REVIEW_REQUIRED" | "HIGH" | "BLOCKED";

export type DraftState =
  | "DRAFT_NOT_SUBMITTED"
  | "QUEUED_FOR_SYNC"
  | "SYNC_IN_PROGRESS"
  | "SUBMISSION_PENDING_VERIFICATION"
  | "SUBMITTED_CONFIRMED"
  | "SUBMISSION_FAILED"
  | "REQUIRES_REVIEW"
  | "CANCELLED";

export interface Remaining {
  state: "VERIFIED" | "SYNTHETIC_UNVERIFIED" | "UNABLE_TO_VERIFY";
  display: string;
  note: string;
}

export interface Entitlement {
  id: string;
  commodity_code: string;
  commodity_name: string;
  period: string;
  unit: string;
  entitled_qty: number | null;
  drawn_qty: number | null;
  remaining: Remaining;
  provenance: Provenance;
  provenance_label: string;
  verification_status: string;
  jurisdiction: string;
  rules_version: string;
  source_ref: string | null;
  last_verified_at: string | null;
  is_synthetic: boolean;
}

export interface Member {
  id: string;
  household_id: string;
  alias: string;
  full_name: string;
  age: number | null;
  age_band: string | null;
  membership_status: string;
  relationship: string | null;
  verification_state: string;
  provenance: Provenance;
  provenance_label: string;
  consent_state: string;
  is_head: boolean;
  is_absent: boolean;
  is_dependent: boolean;
  document: {
    name: string | null;
    age: number | null;
    ref: string | null;
    provenance: Provenance | null;
    provenance_label: string;
  };
  last_verified_at: string | null;
  privacy_notice: string;
  entitlements?: Entitlement[];
}

export interface Household {
  id: string;
  reference: string;
  label: string;
  home_state: string;
  home_jurisdiction_code: string;
  destination_state: string;
  destination_jurisdiction_code: string;
  destination_shop_id: string | null;
  provenance: string;
  provenance_label: string;
  last_verified_at: string | null;
  last_synced_at: string | null;
  member_count: number;
  is_synthetic: boolean;
  session: {
    role: "MEMBER" | "FACILITATOR" | "ADMIN" | "PUBLIC";
    member_id: string | null;
    expires_at: string;
    permissions: string[];
    consent_members: string[];
  };
  current_member: Member;
  own_entitlements: Entitlement[];
  notice: string;
}

export interface SessionPayload {
  token?: string;
  session_id?: string;
  role: "MEMBER" | "FACILITATOR" | "ADMIN" | "PUBLIC";
  household: {
    id: string;
    reference: string;
    label: string;
    home_state: string;
    destination_state: string;
  };
  member: Member | null;
  permissions: string[];
  consent_member_ids: string[];
  purpose: string;
  expires_at: string;
  demo_notice: string;
  policy_version?: string;
  cleanup_notice?: string;
}

export interface DemoMemberSummary {
  id: string;
  alias: string;
  relationship: string | null;
  age_band: string;
  is_head: boolean;
  is_absent: boolean;
  is_dependent: boolean;
  verification_state: string;
}

export interface DemoHousehold {
  id: string;
  reference: string;
  label: string;
  home_state: string;
  destination_state: string;
  is_synthetic: boolean;
  members: DemoMemberSummary[];
}

export interface Decision {
  decision: string;
  eligible_to_proceed: boolean;
  travel_recommended: boolean;
  headline: string;
  reasons: string[];
  assumptions: string[];
  required_evidence: string[];
  authority_to_contact: string[];
  alternative_pathways: { id: string; title: string; detail: string; certainty: string }[];
  cannot_guarantee: string[];
  stock: {
    state: string;
    label: string;
    observed_at: string | null;
    age_hours: number | null;
    freshness_hours: number;
    source: string;
    provenance: string;
    note: string | null;
  } | null;
  rule: {
    version: string;
    source_label: string;
    is_synthetic: boolean;
    effective_from?: string;
    disclaimers?: string[];
  };
  commodity: { code?: string; name?: string; unit?: string };
  context: {
    household_ref: string;
    member_id: string;
    member_alias: string;
    home_state: string;
    destination_state: string;
    shop: { id: string | null; name: string; address_label: string | null };
    entitlement: {
      id: string | null;
      period: string | null;
      provenance: string | null;
      verification_status: string | null;
      remaining_verified: boolean;
    };
    evaluated_at: string;
    all_commodities: string[];
  };
  evidence_status: { id: string; label: string; present: boolean; note?: string }[];
}

export interface Finding {
  code: string;
  severity: RiskLevel;
  message: string;
  blocking: boolean;
  member_ref: string | null;
  entitlement_ref: string | null;
}

export interface EvidenceItem {
  id: string;
  label: string;
  required: boolean;
  provided: boolean;
}

export interface Simulation {
  proposal_id: string;
  member_id: string;
  operation: string;
  status: string;
  risk_level: RiskLevel;
  blocked: boolean;
  requires_review: boolean;
  safe_to_submit: boolean;
  findings: Finding[];
  evidence: EvidenceItem[];
  before: HouseholdSnapshot;
  after: HouseholdSnapshot;
  diff: {
    members_added: string[];
    members_removed: string[];
    members_modified: string[];
    member_count_before: number;
    member_count_after: number;
    entitlement_links_before: number;
    entitlement_links_after: number;
    entitlement_links_removed: string[];
    entitlement_periods_affected: string[];
    draw_history_links_affected: string[];
    unresolved_identity_conflicts: string[];
  };
  summary: string[];
  recommended_action: string;
  created_at: string;
  submission_receipt: Record<string, unknown> | null;
  label: string;
}

export interface HouseholdSnapshot {
  household_ref: string;
  member_count: number;
  entitlement_link_count: number;
  members: {
    member_id: string;
    alias: string;
    name: string;
    age: number | null;
    membership_status: string;
    entitlement_links: { id: string; commodity: string; period: string; drawn_qty: number | null }[];
  }[];
}

export interface Draft {
  id: string;
  draft_ref: string;
  kind: string;
  state: DraftState;
  state_label: string;
  payload: Record<string, unknown>;
  version: number;
  member_id: string | null;
  created_at: string;
  updated_at: string;
  last_error: string | null;
  official_receipt_id: string | null;
  is_official_submission: boolean;
  notice: string;
  receipt?: {
    receipt_number: string;
    is_simulated: boolean;
    verified: boolean;
    adapter?: string;
    message?: string;
  } | null;
  verified?: boolean;
  message?: string;
  synced?: boolean;
}

export interface Grievance {
  id: string;
  category: string;
  subject: string;
  filed_at: string | null;
  provenance: string;
  official_receipt_number: string | null;
  local_draft_ref: string | null;
  responsible_office: string | null;
  office_verified: boolean;
  ownership: string;
  assigned_officer: string | null;
  status: string;
  last_status_update: string | null;
  response_recorded: boolean;
  response_summary: string | null;
  resolution_summary: string | null;
  deadline: {
    deadline_verified: boolean;
    deadline_at: string | null;
    deadline_label: string | null;
    filed_days_ago: number | null;
    overdue: boolean;
    deadline_note: string;
    policy: {
      version: string;
      days: number;
      source_label: string;
      verified: boolean;
      is_synthetic: boolean;
    } | null;
  };
  is_synthetic: boolean;
  disclaimer: string;
  events?: { event_type: string; occurred_at: string; detail: Record<string, unknown> }[];
  escalations?: {
    id: string;
    state: string;
    body: string;
    created_at: string;
    submitted_receipt: Record<string, unknown> | null;
  }[];
}

export interface Escalation {
  id: string;
  grievance_id: string;
  body: string;
  state: string;
  state_label: string;
  deadline_verified: boolean;
  deadline_note: string;
  placeholders: Record<string, string | null>;
  notice: string;
}

export interface PublicAggregates {
  generated_at: string;
  window_label: string;
  is_synthetic: boolean;
  disclaimer: string;
  minimum_group_size: number;
  method: Record<string, string>;
  grievances: {
    total: { value: number | null; suppressed: boolean };
    by_category: { category: string; count: { value: number | null; suppressed: boolean } }[];
    resolved: { value: number | null; suppressed: boolean };
    verified_overdue: { value: number | null; suppressed: boolean };
    awaiting_assignment: { value: number | null; suppressed: boolean };
    median_processing_days: { value: number | null; sample_size: number; suppressed: boolean };
  };
  stock: {
    observations: { value: number | null; suppressed: boolean };
    by_state: { state: string; count: { value: number | null; suppressed: boolean }; label: string }[];
    fresh_within_24h: { value: number | null; suppressed: boolean };
    note: string;
  };
  service_completion: { resolved_cases: { value: number | null; suppressed: boolean }; median_days_note: string };
  sla_policies: {
    category: string;
    jurisdiction: string;
    days: number;
    version: string;
    verified: boolean;
    is_synthetic: boolean;
    source_label: string;
  }[];
  small_group_suppressed: boolean;
}

export interface CleanupResult {
  session_id: string;
  ended: boolean;
  ended_reason: string;
  server_cleanup_verified: boolean;
  server_actions: string[];
  client_actions_required: string[];
  limitations: string[];
  household_reference?: string;
  notice?: string;
}
