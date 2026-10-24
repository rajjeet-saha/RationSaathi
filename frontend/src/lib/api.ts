import type {
  CleanupResult,
  Decision,
  DemoHousehold,
  Draft,
  Escalation,
  Grievance,
  Household,
  Member,
  PublicAggregates,
  SessionPayload,
  Simulation,
} from "./types";

const BASE = import.meta.env.VITE_API_BASE ?? "/api/v1";

/**
 * The session token is deliberately held in memory only.
 * It is never written to localStorage, sessionStorage, IndexedDB or a URL, so a
 * refresh or a shared-device handover cannot restore another member's profile.
 */
let sessionToken: string | null = null;
let unauthorizedHandler: (() => void) | null = null;

export class ApiError extends Error {
  status: number;
  payload: unknown;
  constructor(status: number, message: string, payload: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}

export function setSessionToken(token: string | null) {
  sessionToken = token;
}

export function getSessionToken(): string | null {
  return sessionToken;
}

export function onUnauthorized(handler: (() => void) | null) {
  unauthorizedHandler = handler;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  if (init.body) headers.set("Content-Type", "application/json");
  if (sessionToken) headers.set("X-Ration-Session", sessionToken);

  let response: Response;
  try {
    response = await fetch(`${BASE}${path}`, { ...init, headers });
  } catch {
    throw new ApiError(
      0,
      "Cannot reach the RationSaathi server. Check your connection and try again. Nothing was submitted.",
      null,
    );
  }

  // A static host (e.g. a Netlify deploy without the FastAPI backend) answers unknown
  // /api paths with the SPA's index.html. Treat that as "server unreachable" instead of
  // handing HTML to callers that expect JSON, which would crash the whole app.
  const contentType = response.headers.get("Content-Type") ?? "";
  if (contentType.includes("text/html")) {
    throw new ApiError(
      response.ok ? 503 : response.status,
      "The RationSaathi API server is not available on this site. Nothing was submitted.",
      null,
    );
  }

  const text = await response.text();
  let body: unknown = null;
  if (text) {
    try {
      body = JSON.parse(text);
    } catch {
      body = { detail: text };
    }
  }

  if (!response.ok) {
    if (response.status === 401) {
      sessionToken = null;
      unauthorizedHandler?.();
    }
    const detail =
      body && typeof body === "object" && "detail" in body
        ? String((body as { detail: unknown }).detail)
        : `Request failed with status ${response.status}`;
    throw new ApiError(response.status, detail, body);
  }
  return body as T;
}

function json(body: unknown): RequestInit {
  return { method: "POST", body: JSON.stringify(body) };
}

function patch(body: unknown): RequestInit {
  return { method: "PATCH", body: JSON.stringify(body) };
}

export const api = {
  health: () => request<Record<string, unknown>>("/health"),

  startSession: (body: {
    household_id: string;
    role: "MEMBER" | "FACILITATOR";
    member_id?: string | null;
    purpose?: string;
    facilitator_device?: string;
  }) => request<SessionPayload>("/sessions", json(body)),

  currentSession: () => request<SessionPayload>("/sessions/current"),
  permissions: () => request<Record<string, unknown>>("/sessions/me/permissions"),
  consent: (body: { member_id: string; consent_explained: boolean; consent_given: boolean }) =>
    request<{ member: Member; scope: string; scope_notice: string }>("/sessions/consent", json(body)),
  switchProfile: (member_id: string) =>
    request<SessionPayload & { cleanup_notice: string }>("/sessions/switch", json({ member_id })),
  endSession: (body: { reason: string; client_cleanup_confirmed: boolean }) =>
    request<CleanupResult>("/sessions/end", json(body)),

  household: () => request<Household>("/households/current"),
  member: (id: string) => request<Member>(`/members/${id}`),
  entitlements: (id: string) =>
    request<{ entitlements: Member["entitlements"]; notice: string }>(`/members/${id}/entitlements`),

  evaluatePortability: (member_id: string, commodity_code: string) =>
    request<Decision>("/portability/evaluate", json({ member_id, commodity_code })),
  rules: () => request<Record<string, unknown>>("/portability/rules"),
  stockStatus: (shopId: string) => request<Record<string, unknown>>(`/shops/${shopId}/stock-status`),

  simulateCorrection: (body: {
    operation: string;
    member_id: string;
    fields?: Record<string, unknown>;
    new_member?: Record<string, unknown> | null;
    merge_into_member_id?: string | null;
    evidence?: string[];
    reason?: string | null;
  }) => request<Simulation>("/corrections/simulate", json(body)),
  saveCorrectionDraft: (proposalId: string, body: { evidence: string[]; note?: string }) =>
    request<{ draft_ref: string; draft_id: string; state: string; proposal: Simulation }>(
      `/corrections/${proposalId}/draft`,
      json(body),
    ),
  submitCorrection: (proposalId: string) =>
    request<Record<string, unknown>>(`/corrections/${proposalId}/submit`, { method: "POST" }),

  drafts: () => request<{ drafts: Draft[]; states: string[]; notice: string }>("/drafts"),
  createDraft: (body: { kind: string; member_id?: string | null; payload: Record<string, unknown>; idempotency_key?: string }) =>
    request<Draft>("/drafts", json(body)),
  updateDraft: (id: string, payload: Record<string, unknown>, expected_version: number) =>
    request<Draft>(`/drafts/${id}`, patch({ payload, expected_version })),
  syncDraft: (id: string, network_online: boolean) =>
    request<Draft>(`/drafts/${id}/sync`, json({ network_online })),
  verifyDraft: (id: string, simulate_receipt: boolean) =>
    request<Draft>(`/drafts/${id}/verify-submission`, json({ simulate_receipt })),
  cancelDraft: (id: string) => request<Draft>(`/drafts/${id}`, { method: "DELETE" }),

  grievances: () => request<{ grievances: Grievance[]; notice: string }>("/grievances"),
  grievance: (id: string) => request<Grievance>(`/grievances/${id}`),
  verifyGrievance: (id: string) =>
    request<Grievance>(`/grievances/${id}/verify-status`, { method: "POST" }),
  createEscalation: (
    id: string,
    body: { recipient_office?: string; officer_placeholder?: string; safe_contact?: string },
  ) => request<Escalation>(`/grievances/${id}/escalation-draft`, json(body)),
  updateEscalation: (id: string, body: string) =>
    request<{ id: string; body: string; state: string; state_label: string }>(
      `/grievances/escalations/${id}`,
      patch({ body }),
    ),
  submitEscalation: (id: string, confirm_authorised_channel: boolean) =>
    request<Record<string, unknown>>(
      `/grievances/escalations/${id}/submit`,
      json({ confirm_authorised_channel }),
    ),

  publicAggregates: () => request<PublicAggregates>("/public/aggregates"),

  demoProfiles: () => request<{ households: DemoHousehold[]; notice: string }>("/demo/profiles"),
  demoStatus: () => request<Record<string, unknown>>("/demo/status"),
  demoScenario: () => request<Record<string, unknown>>("/demo/scenario"),
  demoReset: () => request<{ reset: boolean; summary: Record<string, unknown>; notice: string }>("/demo/reset", {
    method: "POST",
  }),
};
