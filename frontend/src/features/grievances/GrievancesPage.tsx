import { CalendarClock, ChevronRight, CircleHelp, Scale } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ReadAloud } from "../../components/ReadAloud";
import { Card, ErrorState, LoadingState, Notice, PageHeader } from "../../components/ui";
import { api, ApiError } from "../../lib/api";
import { useI18n } from "../../lib/i18n";
import type { Grievance } from "../../lib/types";

const STATUS_STYLE: Record<string, string> = {
  FILED: "border-sky-300 bg-sky-50 text-sky-950",
  ASSIGNED: "border-sky-300 bg-sky-50 text-sky-950",
  ACKNOWLEDGED: "border-sky-300 bg-sky-50 text-sky-950",
  IN_REVIEW: "border-sky-300 bg-sky-50 text-sky-950",
  INFORMATION_REQUESTED: "border-amber-300 bg-warningBg text-amber-950",
  OVERDUE: "border-red-300 bg-dangerBg text-red-950",
  ESCALATION_DRAFT: "border-amber-300 bg-warningBg text-amber-950",
  ESCALATED: "border-amber-300 bg-warningBg text-amber-950",
  RESOLVED: "border-brand-300 bg-brand-50 text-brand-950",
  STATUS_UNKNOWN: "border-slate-300 bg-unknownBg text-slate-800",
  DRAFT: "border-slate-300 bg-unknownBg text-slate-800",
  REOPENED: "border-sky-300 bg-sky-50 text-sky-950",
};

export function GrievancesPage() {
  const { t } = useI18n();
  const [grievances, setGrievances] = useState<Grievance[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = () => {
    setLoading(true);
    api
      .grievances()
      .then((payload) => setGrievances(payload.grievances))
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load grievances."))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  return (
    <div>
      <PageHeader
        eyebrow="Grievance lifecycle"
        title="Track what happened, without inventing deadlines"
        description="A case is overdue only when a configured deadline is verified and has passed. Elapsed days alone are never treated as proof of a violation."
        icon={<Scale aria-hidden="true" className="size-5" />}
        actions={
          <ReadAloud
            compact
            text={`${grievances.length} grievance records. ${t("grievance.deadlineUnknown")} ${t("grievance.escalationDraft")}.`}
          />
        }
      />

      {loading ? <LoadingState /> : null}
      {error ? <ErrorState message={error} onRetry={load} /> : null}

      <div className="space-y-3">
        {grievances.map((grievance) => (
          <Card key={grievance.id}>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <span className={`chip ${STATUS_STYLE[grievance.status] ?? STATUS_STYLE.STATUS_UNKNOWN}`}>
                    {grievance.status.replaceAll("_", " ")}
                  </span>
                  <span className="text-xs text-muted">{grievance.category.replaceAll("_", " ")}</span>
                </div>
                <h2 className="mt-1 text-base font-bold sm:text-lg">{grievance.subject}</h2>
                <p className="text-xs text-muted">
                  Filed {grievance.deadline.filed_days_ago ?? "?"} days ago · receipt{" "}
                  {grievance.official_receipt_number ?? "not verified"} ·{" "}
                  {grievance.office_verified ? grievance.responsible_office : "ownership needs verification"}
                </p>
              </div>
              <Link
                to={`/grievances/${grievance.id}`}
                className="btn-secondary min-h-9 px-3 py-1.5 text-xs"
                aria-label={`Open grievance ${grievance.subject}`}
              >
                Open case
                <ChevronRight aria-hidden="true" className="size-4" />
              </Link>
            </div>

            {grievance.deadline.deadline_verified ? (
              <p className="mt-2 flex items-start gap-2 rounded-lg bg-canvas p-2 text-xs text-muted">
                <CalendarClock aria-hidden="true" className="mt-0.5 size-3.5 shrink-0" />
                Verified configured deadline: {grievance.deadline.deadline_label}. {grievance.deadline.deadline_note}
              </p>
            ) : (
              <p className="mt-2 flex items-start gap-2 rounded-lg bg-warningBg p-2 text-xs font-medium text-amber-950">
                <CircleHelp aria-hidden="true" className="mt-0.5 size-3.5 shrink-0" />
                {t("grievance.deadlineUnknown")}
              </p>
            )}
          </Card>
        ))}
      </div>

      {!loading && grievances.length === 0 ? (
        <Notice tone="info">
          No grievances are visible in this profile scope. The backend filters cases by member.
        </Notice>
      ) : null}

      <Notice tone="warning" className="mt-4" title="Synthetic case data">
        Receipt references, offices and service policies here are fictional demo fixtures. No government case is represented.
      </Notice>
    </div>
  );
}
