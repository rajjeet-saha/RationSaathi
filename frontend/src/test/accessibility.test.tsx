import { render, screen } from "@testing-library/react";
import axe from "axe-core";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { I18nProvider } from "../lib/i18n";
import { CorrectionsPage } from "../features/corrections/CorrectionsPage";

const { mockSession, mockApi } = vi.hoisted(() => ({
  mockSession: { session: { member_id: "mem-a2" } },
  mockApi: {
    household: vi.fn(),
    simulateCorrection: vi.fn(),
    saveCorrectionDraft: vi.fn(),
    submitCorrection: vi.fn(),
  },
}));

vi.mock("../app/session", () => ({ useSession: () => mockSession }));
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

// jsdom does not implement the layout engine axe needs for colour-contrast, and
// this test run focuses on structure/roles/names rather than rendered pixels.
const AXE_OPTIONS: axe.RunOptions = {
  rules: {
    "color-contrast": { enabled: false },
    region: { enabled: false },
  },
};

async function expectNoViolations(container: HTMLElement) {
  const results = await axe.run(container, AXE_OPTIONS);
  const summary = results.violations.map((v) => `${v.id}: ${v.help} (${v.nodes.length} nodes)`);
  expect(summary).toEqual([]);
}

beforeEach(() => {
  vi.clearAllMocks();
  mockApi.household.mockResolvedValue({
    current_member: {
      id: "mem-a2",
      alias: "Ramesh Kumar",
      full_name: "Ramesh Kumar",
      age: 36,
      verification_state: "MISMATCH_FLAGGED",
      document: { name: "Ramesh Kumar", age: 36 },
    },
  });
});

describe("accessibility (axe)", () => {
  it("corrections screen has no detectable violations in its initial state", async () => {
    const { container } = render(
      <I18nProvider>
        <CorrectionsPage />
      </I18nProvider>,
    );
    expect(await screen.findByText("Compare before you change anything")).toBeInTheDocument();
    await expectNoViolations(container);
  });

  it("corrections screen has no detectable violations after a blocked simulation", async () => {
    mockApi.simulateCorrection.mockResolvedValue({
      proposal_id: "prop-1",
      operation: "REPLACE_MEMBER",
      risk_level: "BLOCKED",
      blocked: true,
      requires_review: false,
      recommended_action: "Preserve the original record.",
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
        { code: "member_removed", severity: "BLOCKED", message: "This proposal removes a household member." },
      ],
      evidence: [],
    });

    const user = (await import("@testing-library/user-event")).default.setup();
    const { container } = render(
      <I18nProvider>
        <CorrectionsPage />
      </I18nProvider>,
    );
    await user.click(await screen.findByRole("button", { name: /Try replace and delete/i }));
    expect(await screen.findByText("This change is blocked")).toBeInTheDocument();
    await expectNoViolations(container);
  });
});
