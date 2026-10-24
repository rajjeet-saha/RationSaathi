import { BarChart3, EyeOff, Lock, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { DemoBanner } from "../../components/DemoBanner";
import { ReadAloud } from "../../components/ReadAloud";
import { Card, ErrorState, LoadingState, Notice, PageHeader, cn } from "../../components/ui";
import { api, ApiError } from "../../lib/api";
import type { PublicAggregates } from "../../lib/types";

function CellValue({ cell }: { cell: { value: number | null; suppressed: boolean } }) {
  if (cell.suppressed) {
    return (
      <span className="inline-flex items-center gap-1 text-xs font-semibold text-muted">
        <EyeOff aria-hidden="true" className="size-3.5" />
        Suppressed (small group)
      </span>
    );
  }
  return <span className="text-2xl font-bold">{cell.value}</span>;
}

export function PublicPage({ standalone = false }: { standalone?: boolean }) {
  const [data, setData] = useState<PublicAggregates | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    setError("");
    api
      .publicAggregates()
      .then(setData)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load public statistics."))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const content = (
    <div>
      <PageHeader
        eyebrow="Public observer · de-identified"
        title="Service statistics without identifying anyone"
        description="Only aggregates are published. Cells below the minimum group size are suppressed, and no names, receipt numbers, household references or narratives are present."
        icon={<BarChart3 aria-hidden="true" className="size-5" />}
        actions={data ? <ReadAloud compact text={`Public synthetic statistics. ${data.disclaimer}`} /> : null}
      />

      {loading ? <LoadingState /> : null}
      {error ? <ErrorState message={error} onRetry={load} /> : null}

      {data ? (
        <>
          <Notice tone="warning" title="Synthetic aggregation">
            {data.disclaimer}
          </Notice>

          <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Card>
              <p className="text-xs font-bold uppercase tracking-wide text-muted">Total grievances</p>
              <div className="mt-1"><CellValue cell={data.grievances.total} /></div>
            </Card>
            <Card>
              <p className="text-xs font-bold uppercase tracking-wide text-muted">Resolved</p>
              <div className="mt-1"><CellValue cell={data.grievances.resolved} /></div>
            </Card>
            <Card>
              <p className="text-xs font-bold uppercase tracking-wide text-muted">Verified overdue</p>
              <div className="mt-1"><CellValue cell={data.grievances.verified_overdue} /></div>
              <p className="mt-1 text-xs text-muted">Only cases with a verified configured deadline.</p>
            </Card>
            <Card>
              <p className="text-xs font-bold uppercase tracking-wide text-muted">Median processing days</p>
              <div className="mt-1">
                {data.grievances.median_processing_days.suppressed ? (
                  <span className="text-xs font-semibold text-muted">
                    Not enough resolved cases (n={data.grievances.median_processing_days.sample_size})
                  </span>
                ) : (
                  <span className="text-2xl font-bold">{data.grievances.median_processing_days.value}</span>
                )}
              </div>
            </Card>
          </div>

          <div className="mt-4 grid gap-4 lg:grid-cols-2">
            <Card>
              <h2 className="section-title">Grievances by category</h2>
              <ul className="mt-2 space-y-2">
                {data.grievances.by_category.map((row) => (
                  <li key={row.category} className="flex items-center justify-between gap-2 rounded-lg border border-line p-2.5">
                    <span className="text-sm font-medium">{row.category.replaceAll("_", " ")}</span>
                    <CellValue cell={row.count} />
                  </li>
                ))}
              </ul>
              <p className="mt-2 text-xs text-muted">
                Awaiting assignment: {data.grievances.awaiting_assignment.suppressed ? "suppressed" : data.grievances.awaiting_assignment.value}
              </p>
            </Card>

            <Card>
              <h2 className="section-title">Stock-report freshness</h2>
              <p className="text-xs text-muted">{data.stock.note}</p>
              <ul className="mt-2 space-y-2">
                {data.stock.by_state.map((row) => (
                  <li key={row.state} className="flex items-center justify-between gap-2 rounded-lg border border-line p-2.5">
                    <span className={cn("text-sm font-medium")}>{row.label.replaceAll("_", " ")}</span>
                    <CellValue cell={row.count} />
                  </li>
                ))}
              </ul>
              <p className="mt-2 text-xs text-muted">
                Fresh within 24h:{" "}
                {data.stock.fresh_within_24h.suppressed ? "suppressed" : data.stock.fresh_within_24h.value} of{" "}
                {data.stock.observations.suppressed ? "suppressed" : data.stock.observations.value} observations.
              </p>
            </Card>
          </div>

          <Card className="mt-4">
            <h2 className="section-title flex items-center gap-2">
              <Lock aria-hidden="true" className="size-5 text-brand-800" />
              Privacy method
            </h2>
            <dl className="mt-2 space-y-2 text-sm">
              {Object.entries(data.method).map(([key, value]) => (
                <div key={key} className="rounded-lg border border-line p-2.5">
                  <dt className="text-xs font-bold uppercase tracking-wide text-muted">{key}</dt>
                  <dd className="mt-0.5">{value}</dd>
                </div>
              ))}
              <div className="rounded-lg border border-line p-2.5">
                <dt className="text-xs font-bold uppercase tracking-wide text-muted">minimum group size</dt>
                <dd className="mt-0.5">{data.minimum_group_size}</dd>
              </div>
            </dl>
            <p className="mt-2 text-xs text-muted">
              Suppression is applied independently to category cells so that a hidden value cannot be recovered by
              subtracting published totals.
            </p>
          </Card>

          <Card className="mt-4">
            <h2 className="section-title">Configured service policies (synthetic)</h2>
            <ul className="mt-2 space-y-2">
              {data.sla_policies.map((policy) => (
                <li key={`${policy.category}-${policy.version}`} className="rounded-lg border border-line p-2.5 text-sm">
                  <p className="font-semibold">
                    {policy.category.replaceAll("_", " ")} · {policy.days} days
                  </p>
                  <p className="text-xs text-muted">
                    {policy.jurisdiction} · version {policy.version} · {policy.source_label}
                  </p>
                </li>
              ))}
            </ul>
            <p className="mt-2 text-xs text-muted">
              These are demo policies, not legal service standards. Public figures distinguish verified overdue cases from
              unverified deadlines.
            </p>
          </Card>
        </>
      ) : null}
    </div>
  );

  if (!standalone) return content;

  return (
    <div className="min-h-screen bg-canvas">
      <DemoBanner />
      <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
          <Link to="/signin" className="link inline-flex items-center gap-2 text-sm">
            <ShieldCheck aria-hidden="true" className="size-4" />
            RationSaathi demo home
          </Link>
          <span className="chip border-slate-300 bg-unknownBg text-slate-700">Public observer — no session</span>
        </div>
        {content}
      </div>
    </div>
  );
}
