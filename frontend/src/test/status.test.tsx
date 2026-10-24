import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { I18nProvider } from "../lib/i18n";
import { RiskBadge, TranslatedDraftBadge } from "../components/status";
import type { DraftState } from "../lib/types";

function renderWithI18n(ui: React.ReactNode) {
  return render(<I18nProvider>{ui}</I18nProvider>);
}

describe("RiskBadge", () => {
  it("labels BLOCKED with text, not colour alone", () => {
    renderWithI18n(<RiskBadge level="BLOCKED" />);
    // Safety-critical: the risk level must be readable text for screen readers.
    expect(screen.getByText(/blocked/i)).toBeInTheDocument();
    // Screen-reader prefix disambiguates the label from surrounding copy.
    expect(screen.getByText(/Risk/)).toBeInTheDocument();
  });

  it("labels REVIEW_REQUIRED as a distinct, readable status", () => {
    renderWithI18n(<RiskBadge level="REVIEW_REQUIRED" />);
    expect(screen.getByText(/review required/i)).toBeInTheDocument();
  });

  it("labels LOW risk explicitly", () => {
    renderWithI18n(<RiskBadge level="LOW" />);
    expect(screen.getByText(/low risk/i)).toBeInTheDocument();
  });

  it("falls back to a safe status for an unknown level", () => {
    renderWithI18n(<RiskBadge level={"NOT_A_REAL_LEVEL" as never} />);
    // Unknown input must not silently render as "safe"/LOW.
    expect(screen.getByText(/review required/i)).toBeInTheDocument();
  });
});

describe("TranslatedDraftBadge", () => {
  const states: DraftState[] = [
    "DRAFT_NOT_SUBMITTED",
    "QUEUED_FOR_SYNC",
    "SYNC_IN_PROGRESS",
    "SUBMISSION_PENDING_VERIFICATION",
    "SUBMITTED_CONFIRMED",
    "SUBMISSION_FAILED",
    "REQUIRES_REVIEW",
    "CANCELLED",
  ];

  it("renders an explicit, non-collapsed label for every draft state", () => {
    for (const state of states) {
      const { unmount } = renderWithI18n(<TranslatedDraftBadge state={state} />);
      const label = screen.getByText(/Saved on this device|Waiting for a connection|Syncing draft data|Submission response received|Official submission confirmed|Submission failed|Needs review|Cancelled/i);
      expect(label).toBeInTheDocument();
      unmount();
    }
  });

  it("never collapses a draft into a generic 'Pending' label", () => {
    const { container } = renderWithI18n(<TranslatedDraftBadge state="SUBMISSION_PENDING_VERIFICATION" />);
    expect(container.textContent).not.toMatch(/^pending$/i);
  });

  it("marks a confirmed submission as confirmed, distinct from a draft", () => {
    renderWithI18n(<TranslatedDraftBadge state="DRAFT_NOT_SUBMITTED" />);
    expect(screen.getByText(/not submitted/i)).toBeInTheDocument();
  });
});
