import {
  AlertTriangle,
  BadgeCheck,
  Ban,
  CircleHelp,
  Clock3,
  CloudOff,
  FileClock,
  FileWarning,
  PackageCheck,
  PackageX,
  ShieldAlert,
  ShieldCheck,
} from "lucide-react";
import type { ReactNode } from "react";
import type { DraftState, Provenance, RiskLevel } from "../lib/types";
import type { TranslationKey } from "../locales/en";
import { useI18n } from "../lib/i18n";
import { cn } from "./ui";

interface BadgeProps {
  label: string;
  icon?: ReactNode;
  className?: string;
  srPrefix?: string;
}

export function StatusBadge({ label, icon, className, srPrefix }: BadgeProps) {
  return (
    <span className={cn("chip", className)}>
      {icon}
      {srPrefix ? <span className="sr-only">{srPrefix}: </span> : null}
      <span>{label}</span>
    </span>
  );
}

const PROVENANCE_STYLE: Record<Provenance, { className: string; icon: ReactNode; short: string }> = {
  OFFICIAL_VERIFIED: {
    className: "border-brand-300 bg-brand-50 text-brand-950",
    icon: <BadgeCheck aria-hidden="true" className="size-3.5" />,
    short: "Verified",
  },
  OFFICIAL_LAST_SYNCED: {
    className: "border-sky-300 bg-sky-50 text-sky-950",
    icon: <CloudOff aria-hidden="true" className="size-3.5" />,
    short: "Last synced",
  },
  HOUSEHOLD_REPORTED: {
    className: "border-amber-300 bg-warningBg text-amber-950",
    icon: <FileWarning aria-hidden="true" className="size-3.5" />,
    short: "Household reported",
  },
  FACILITATOR_ENTERED: {
    className: "border-amber-300 bg-amber-50 text-amber-950",
    icon: <FileClock aria-hidden="true" className="size-3.5" />,
    short: "Facilitator entered",
  },
  SYNTHETIC_DEMO: {
    className: "border-slate-300 bg-slate-100 text-slate-800",
    icon: <CircleHelp aria-hidden="true" className="size-3.5" />,
    short: "Synthetic",
  },
  UNKNOWN: {
    className: "border-slate-300 bg-unknownBg text-slate-700",
    icon: <CircleHelp aria-hidden="true" className="size-3.5" />,
    short: "Unknown",
  },
};

export function ProvenanceBadge({ provenance, label }: { provenance: Provenance; label?: string }) {
  const style = PROVENANCE_STYLE[provenance] ?? PROVENANCE_STYLE.UNKNOWN;
  return (
    <StatusBadge
      label={label ?? style.short}
      icon={style.icon}
      className={style.className}
      srPrefix="Source"
    />
  );
}

const RISK_STYLE: Record<RiskLevel, { className: string; icon: ReactNode; label: string }> = {
  LOW: {
    className: "border-brand-300 bg-brand-50 text-brand-950",
    icon: <ShieldCheck aria-hidden="true" className="size-4" />,
    label: "Low risk",
  },
  REVIEW_REQUIRED: {
    className: "border-amber-300 bg-warningBg text-amber-950",
    icon: <AlertTriangle aria-hidden="true" className="size-4" />,
    label: "Review required",
  },
  HIGH: {
    className: "border-orange-300 bg-orange-50 text-orange-950",
    icon: <ShieldAlert aria-hidden="true" className="size-4" />,
    label: "High risk",
  },
  BLOCKED: {
    className: "border-red-300 bg-dangerBg text-red-950",
    icon: <Ban aria-hidden="true" className="size-4" />,
    label: "Blocked",
  },
};

export function RiskBadge({ level, label }: { level: RiskLevel; label?: string }) {
  const style = RISK_STYLE[level] ?? RISK_STYLE.REVIEW_REQUIRED;
  return (
    <StatusBadge label={label ?? style.label} icon={style.icon} className={style.className} srPrefix="Risk" />
  );
}

const DECISION_STYLE: Record<string, { className: string; icon: ReactNode; label: string }> = {
  ELIGIBLE_TO_PROCEED: {
    className: "border-brand-300 bg-brand-50 text-brand-950",
    icon: <ShieldCheck aria-hidden="true" className="size-4" />,
    label: "Eligible to proceed (configured rules)",
  },
  POTENTIALLY_ELIGIBLE_VERIFICATION_REQUIRED: {
    className: "border-amber-300 bg-warningBg text-amber-950",
    icon: <AlertTriangle aria-hidden="true" className="size-4" />,
    label: "Potentially eligible — verification required",
  },
  MORE_INFORMATION_REQUIRED: {
    className: "border-amber-300 bg-amber-50 text-amber-950",
    icon: <CircleHelp aria-hidden="true" className="size-4" />,
    label: "More information required",
  },
  NOT_SUPPORTED_BY_CONFIGURED_RULES: {
    className: "border-slate-300 bg-slate-100 text-slate-800",
    icon: <Ban aria-hidden="true" className="size-4" />,
    label: "Not supported by configured rules",
  },
  CANNOT_DETERMINE_FROM_AVAILABLE_DATA: {
    className: "border-slate-300 bg-unknownBg text-slate-800",
    icon: <CircleHelp aria-hidden="true" className="size-4" />,
    label: "Cannot determine from available data",
  },
};

export function DecisionBadge({ decision }: { decision: string }) {
  const style = DECISION_STYLE[decision] ?? DECISION_STYLE.CANNOT_DETERMINE_FROM_AVAILABLE_DATA;
  return <StatusBadge label={style.label} icon={style.icon} className={style.className} srPrefix="Decision" />;
}

const STOCK_STYLE: Record<string, { className: string; icon: ReactNode }> = {
  AVAILABLE_VERIFIED: { className: "border-brand-300 bg-brand-50 text-brand-950", icon: <PackageCheck aria-hidden="true" className="size-4" /> },
  REPORTED_AVAILABLE: { className: "border-amber-300 bg-warningBg text-amber-950", icon: <PackageCheck aria-hidden="true" className="size-4" /> },
  OUT_OF_STOCK_REPORTED: { className: "border-orange-300 bg-orange-50 text-orange-950", icon: <PackageX aria-hidden="true" className="size-4" /> },
  OUT_OF_STOCK_VERIFIED: { className: "border-red-300 bg-dangerBg text-red-950", icon: <PackageX aria-hidden="true" className="size-4" /> },
  STALE: { className: "border-amber-300 bg-warningBg text-amber-950", icon: <Clock3 aria-hidden="true" className="size-4" /> },
  UNKNOWN: { className: "border-slate-300 bg-unknownBg text-slate-800", icon: <CircleHelp aria-hidden="true" className="size-4" /> },
  SOURCE_UNAVAILABLE: { className: "border-slate-300 bg-unknownBg text-slate-700", icon: <CloudOff aria-hidden="true" className="size-4" /> },
};

export function StockBadge({ state, label }: { state: string; label: string }) {
  const style = STOCK_STYLE[state] ?? STOCK_STYLE.UNKNOWN;
  return <StatusBadge label={label} icon={style.icon} className={style.className} srPrefix="Stock" />;
}

const DRAFT_STYLE: Record<DraftState, string> = {
  DRAFT_NOT_SUBMITTED: "border-amber-300 bg-warningBg text-amber-950",
  QUEUED_FOR_SYNC: "border-sky-300 bg-sky-50 text-sky-950",
  SYNC_IN_PROGRESS: "border-sky-300 bg-sky-50 text-sky-950",
  SUBMISSION_PENDING_VERIFICATION: "border-amber-300 bg-amber-50 text-amber-950",
  SUBMITTED_CONFIRMED: "border-brand-300 bg-brand-50 text-brand-950",
  SUBMISSION_FAILED: "border-red-300 bg-dangerBg text-red-950",
  REQUIRES_REVIEW: "border-orange-300 bg-orange-50 text-orange-950",
  CANCELLED: "border-slate-300 bg-unknownBg text-slate-700",
};

export function DraftBadge({ state, label }: { state: DraftState; label: string }) {
  const icon =
    state === "SUBMITTED_CONFIRMED" ? (
      <BadgeCheck aria-hidden="true" className="size-4" />
    ) : state === "SUBMISSION_FAILED" ? (
      <Ban aria-hidden="true" className="size-4" />
    ) : state === "DRAFT_NOT_SUBMITTED" ? (
      <FileWarning aria-hidden="true" className="size-4" />
    ) : (
      <Clock3 aria-hidden="true" className="size-4" />
    );
  return <StatusBadge label={label} icon={icon} className={DRAFT_STYLE[state]} srPrefix="Draft status" />;
}

export function TranslatedDraftBadge({ state }: { state: DraftState }) {
  const { t } = useI18n();
  const map: Record<DraftState, TranslationKey> = {
    DRAFT_NOT_SUBMITTED: "draft.notSubmitted",
    QUEUED_FOR_SYNC: "draft.queued",
    SYNC_IN_PROGRESS: "draft.syncing",
    SUBMISSION_PENDING_VERIFICATION: "draft.pending",
    SUBMITTED_CONFIRMED: "draft.confirmed",
    SUBMISSION_FAILED: "draft.failed",
    REQUIRES_REVIEW: "draft.review",
    CANCELLED: "draft.cancelled",
  };
  return <DraftBadge state={state} label={t(map[state])} />;
}
