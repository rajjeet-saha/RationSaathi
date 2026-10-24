import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { I18nProvider } from "../lib/i18n";
import { CorrectionsPage } from "../features/corrections/CorrectionsPage";
import { ApiError } from "../lib/api";

const { mockSession, mockApi } = vi.hoisted(() => ({
  mockSession: { session: { member_id: "mem-a2" } },
  mockApi: {
    household: vi.fn(),
    simulateCorrection: vi.fn(),
    saveCorrectionDraft: vi.fn(),
    submitCorrection: vi.fn(),
  },
}));

vi.mock("../app/session", () => ({
  useSession: () => mockSession,
}));

vi.mock("../lib/api", () => ({
  api: mockApi,
  ApiError: class ApiError extends Error {
    status: number;
    constructor(status: number, message: string) {
      super(message);
      this.status = status;
    }
  },
}));

function householdFixture(overrides: Record<string, unknown> = {}) {
  return {
    current_member: {
      id: "mem-a2",
      alias: "Ramesh Kumar",
      full_name: "Ramesh Kumar",
      age: 36,
      verification_state: "MISMATCH_FLAGGED",
      document: { name: "Ramesh Kumar", age: 36 },
      ...((overrides.member as Record<string, unknown>) ?? {}),
    },
    ...(overrides.root ?? {}),
  };
}

function simulationFixture(overrides: Record<string, unknown> = {}) {
  return {
    proposal_id: "prop-1",
    operation: "REPLACE_MEMBER",
    risk_level: "BLOCKED",
    blocked: true,
    requires_review: false,
    recommended_action: "Preserve the original record. Reconcile the mismatch instead.",
    summary: ["One member would be removed."],
    diff: {
      member_count_before: 5,
      member_count_after: 4,
      members_removed: ["mem-a2"],
      members_added: [],
      entitlement_links_before: 5,
      entitlement_links_after: 4,
      entitlement_links_removed: ["ent-a2-rice"],
      entitlement_periods_affected: ["2026-10"],
      draw_history_links_affected: ["ent-a2-rice"],
      unresolved_identity_conflicts: ["name_mismatch"],
    },
    findings: [
      {
        code: "member_removed",
        severity: "BLOCKED",
        message: "This proposal removes a household member.",
      },
    ],
    evidence: [],
    ...overrides,
  };
}

function renderPage() {
  return render(
    <I18nProvider>
      <CorrectionsPage />
    </I18nProvider>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  mockApi.household.mockResolvedValue(householdFixture());
});

describe("CorrectionsPage", () => {
  it("shows the mismatch and warns that evidence may itself be wrong", async () => {
    renderPage();
    expect(await screen.findByText("Compare before you change anything")).toBeInTheDocument();
    expect(screen.getByText(/Mismatched member record/i)).toBeInTheDocument();
    expect(screen.getByText(/simulator does not assume which value is right/i)).toBeInTheDocument();
  });

  it("runs a destructive simulation and shows a BLOCKED risk badge with explicit text", async () => {
    mockApi.simulateCorrection.mockResolvedValue(simulationFixture());
    renderPage();
    const user = userEvent.setup();

    await user.click(await screen.findByRole("button", { name: /Try replace and delete/i }));

    expect(await screen.findByText("This change is blocked")).toBeInTheDocument();
    expect(screen.getAllByText("Blocked").length).toBeGreaterThan(0);
    expect(screen.getByText(/The original member record is preserved/i)).toBeInTheDocument();
    // The server's blocking decision is surfaced verbatim, not softened to a warning.
    expect(screen.getByText(/This proposal removes a household member/i)).toBeInTheDocument();
  });

  it("disables submission and draft-saving for a blocked proposal", async () => {
    mockApi.simulateCorrection.mockResolvedValue(simulationFixture());
    renderPage();
    const user = userEvent.setup();

    await user.click(await screen.findByRole("button", { name: /Try replace and delete/i }));
    const submitButton = await screen.findByRole("button", { name: /Demo test: attempt submission/i });
    expect(submitButton).toBeDisabled();

    const saveButton = screen.getByRole("button", { name: /Save as a labelled draft/i });
    await waitFor(() => expect(saveButton).toBeDisabled());
  });

  it("never labels a draft as a submission when a safe proposal is saved", async () => {
    mockApi.simulateCorrection.mockResolvedValue(
      simulationFixture({
        proposal_id: "prop-2",
        operation: "UPDATE_FIELD",
        risk_level: "LOW",
        blocked: false,
        requires_review: false,
        recommended_action: "Safe to save as a draft.",
        findings: [],
        diff: {
          member_count_before: 5,
          member_count_after: 5,
          members_removed: [],
          members_added: [],
          entitlement_links_before: 5,
          entitlement_links_after: 5,
          entitlement_links_removed: [],
          entitlement_periods_affected: [],
          draw_history_links_affected: [],
          unresolved_identity_conflicts: [],
        },
      }),
    );
    mockApi.saveCorrectionDraft.mockResolvedValue({
      draft_ref: "RS-D-1042",
      draft_id: "draft-1",
      state: "DRAFT_NOT_SUBMITTED",
      proposal: {},
    });
    renderPage();
    const user = userEvent.setup();

    await user.click(await screen.findByRole("button", { name: /Use document values/i }));
    const saveButton = await screen.findByRole("button", { name: /Save as a labelled draft/i });
    expect(saveButton).toBeEnabled();
    await user.click(saveButton);

    // The confirmation must say "not submitted" — never imply official submission.
    // The confirmation must say "not submitted" — never imply official submission.
    expect(await screen.findByText(/^Saved RS-D-1042 as .*not submitted\.$/)).toBeInTheDocument();
    expect(mockApi.submitCorrection).not.toHaveBeenCalled();
  });

  it("surfaces the server rejection when submission is attempted and refused", async () => {
    mockApi.simulateCorrection.mockResolvedValue(
      simulationFixture({
        risk_level: "LOW",
        blocked: false,
        requires_review: false,
        diff: {
          member_count_before: 5,
          member_count_after: 5,
          members_removed: [],
          members_added: [],
          entitlement_links_before: 5,
          entitlement_links_after: 5,
          entitlement_links_removed: [],
          entitlement_periods_affected: [],
          draw_history_links_affected: [],
          unresolved_identity_conflicts: [],
        },
        findings: [],
      }),
    );
    mockApi.submitCorrection.mockRejectedValue(new ApiError(403, "not permitted", null));
    renderPage();
    const user = userEvent.setup();

    await user.click(await screen.findByRole("button", { name: /Use document values/i }));
    const submitButton = await screen.findByRole("button", { name: /Demo test: attempt submission/i });
    expect(submitButton).toBeEnabled();
    await user.click(submitButton);

    // A refused submission is shown as an error, not a success.
    await waitFor(() => expect(screen.getByText(/403: not permitted/i)).toBeInTheDocument());
  });
});
