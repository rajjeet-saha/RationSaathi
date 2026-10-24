import { FlaskConical, RefreshCw, ShieldCheck, TriangleAlert } from "lucide-react";
import { useEffect, useState } from "react";
import { Button, Card, ErrorState, LoadingState, Modal, Notice, PageHeader } from "../../components/ui";
import { api, ApiError } from "../../lib/api";

export function DemoPage() {
  const [scenario, setScenario] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [busy, setBusy] = useState(false);

  const load = () => {
    setLoading(true);
    setError("");
    api
      .demoScenario()
      .then(setScenario)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load the demo scenario."))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const reset = async () => {
    setBusy(true);
    setError("");
    try {
      const result = await api.demoReset();
      setNotice(JSON.stringify(result.summary, null, 2));
      setConfirmOpen(false);
      setNotice(JSON.stringify(result.summary, null, 2));
      // The reset invalidated every session. A full reload clears in-memory state.
      window.location.assign("/signin");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Reset failed.");
      setConfirmOpen(false);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div>
      <PageHeader
        eyebrow="Demo & test console"
        title="Synthetic scenario"
        description="Reset recreates the deterministic fixtures and invalidates every session. No real household data is involved."
        icon={<FlaskConical aria-hidden="true" className="size-5" />}
        actions={
          <Button variant="danger" onClick={() => setConfirmOpen(true)}>
            <RefreshCw aria-hidden="true" className="size-4" />
            Reset demo data
          </Button>
        }
      />

      {loading ? <LoadingState /> : null}
      {error ? <ErrorState message={error} onRetry={load} /> : null}
      {notice ? <Notice tone="success" className="mb-4" title="Reset complete">{notice}</Notice> : null}

      {scenario ? (
        <div className="grid gap-4 lg:grid-cols-2">
          <Card>
            <h2 className="section-title">Seeded facts</h2>
            <dl className="mt-2 space-y-2 text-sm">
              {Object.entries(scenario)
                .filter(([key]) => !["checks", "grievances", "stock_states"].includes(key))
                .map(([key, value]) => (
                  <div key={key} className="rounded-lg border border-line p-2.5">
                    <dt className="text-xs font-bold uppercase tracking-wide text-muted">{key.replaceAll("_", " ")}</dt>
                    <dd className="mt-0.5 break-words">
                      {typeof value === "object" ? JSON.stringify(value) : String(value)}
                    </dd>
                  </div>
                ))}
            </dl>
          </Card>

          <div className="space-y-4">
            <Card>
              <h2 className="section-title">Demonstration checks</h2>
              <ul className="mt-2 space-y-1.5 text-sm">
                {(scenario.checks as string[] | undefined)?.map((check) => (
                  <li key={check} className="flex items-start gap-2">
                    <ShieldCheck aria-hidden="true" className="mt-0.5 size-4 shrink-0 text-brand-700" />
                    {check}
                  </li>
                ))}
              </ul>
            </Card>

            <Card>
              <h2 className="section-title">Stock states present</h2>
              <p className="mt-1 text-sm text-muted">
                {(scenario.stock_states as string[] | undefined)?.join(", ") ?? "None"}
              </p>
              <h3 className="mt-3 text-sm font-bold">Grievances</h3>
              <ul className="mt-1 space-y-1 text-xs text-muted">
                {(scenario.grievances as { id: string; status: string; deadline_verified: boolean; filed_at: string }[] | undefined)?.map(
                  (grievance) => (
                    <li key={grievance.id}>
                      {grievance.id} · {grievance.status} · deadline{" "}
                      {grievance.deadline_verified ? "verified" : "not verified"} · filed{" "}
                      {new Date(grievance.filed_at).toLocaleDateString()}
                    </li>
                  ),
                )}
              </ul>
            </Card>

            <Card>
              <h2 className="section-title">What remains simulated</h2>
              <ul className="mt-2 space-y-1 text-sm text-muted">
                <li>• Identity selection is a demo sign-in, not authentication.</li>
                <li>• Submissions use a labelled simulated adapter.</li>
                <li>• Portability rules, stock records and service deadlines are synthetic.</li>
                <li>• Speech synthesis is browser-provided and may need network access.</li>
                <li>• No government integration is connected.</li>
              </ul>
            </Card>
          </div>
        </div>
      ) : null}

      <Modal
        open={confirmOpen}
        onClose={() => setConfirmOpen(false)}
        title="Reset the entire demo?"
        description="All sessions are invalidated and every synthetic record is recreated. This is the only destructive demo action."
        footer={
          <>
            <Button variant="secondary" onClick={() => setConfirmOpen(false)}>
              Cancel
            </Button>
            <Button variant="danger" onClick={reset} disabled={busy}>
              <TriangleAlert aria-hidden="true" className="size-4" />
              {busy ? "Resetting…" : "Reset demo data"}
            </Button>
          </>
        }
      >
        <Notice tone="warning">
          Existing drafts, correction simulations and grievances created during this demo will be removed. Nothing outside
          this synthetic database is affected.
        </Notice>
      </Modal>
    </div>
  );
}
