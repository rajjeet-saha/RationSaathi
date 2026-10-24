import { CloudOff, Cloud, RefreshCw, ShieldCheck, Trash2, Wifi, WifiOff } from "lucide-react";
import { useEffect, useState } from "react";
import { useSession } from "../../app/session";
import { ReadAloud } from "../../components/ReadAloud";
import { TranslatedDraftBadge } from "../../components/status";
import { Button, Card, DataRow, ErrorState, LoadingState, Notice, PageHeader, cn } from "../../components/ui";
import { api, ApiError } from "../../lib/api";
import { useI18n } from "../../lib/i18n";
import type { Draft, DraftState } from "../../lib/types";

const ALL_STATES: DraftState[] = [
  "DRAFT_NOT_SUBMITTED",
  "QUEUED_FOR_SYNC",
  "SYNC_IN_PROGRESS",
  "SUBMISSION_PENDING_VERIFICATION",
  "SUBMITTED_CONFIRMED",
  "SUBMISSION_FAILED",
  "REQUIRES_REVIEW",
  "CANCELLED",
];

export function DraftsPage() {
  const { session } = useSession();
  const { t } = useI18n();
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [online, setOnline] = useState(true);
  const [simulateReceipt, setSimulateReceipt] = useState(false);
  const [busyId, setBusyId] = useState<string | null>(null);

  const load = () => {
    setLoading(true);
    setError("");
    api
      .drafts()
      .then((payload) => setDrafts(payload.drafts))
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load drafts."))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const updateDraftInList = (next: Draft) => {
    setDrafts((current) => current.map((draft) => (draft.id === next.id ? { ...draft, ...next } : draft)));
  };

  const run = async (draft: Draft, action: "sync" | "verify" | "cancel") => {
    setBusyId(draft.id);
    setError("");
    setNotice("");
    try {
      if (action === "sync") {
        const result = await api.syncDraft(draft.id, online);
        updateDraftInList(result);
        setNotice(result.message ?? "");
      } else if (action === "verify") {
        const result = await api.verifyDraft(draft.id, simulateReceipt);
        updateDraftInList(result);
        setNotice(result.message ?? "");
      } else {
        const result = await api.cancelDraft(draft.id);
        updateDraftInList(result);
        setNotice("Draft content was cleared from the server. Any confirmed receipt is untouched.");
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "The action could not be completed.");
    } finally {
      setBusyId(null);
    }
  };

  if (!session) return null;

  return (
    <div>
      <PageHeader
        eyebrow="Offline and assisted service"
        title="Draft manager"
        description="Every state is explicit. A draft reference is never an official receipt, and reconnecting is never treated as proof of submission."
        icon={<CloudOff aria-hidden="true" className="size-5" />}
        actions={<ReadAloud compact text={`${t("draft.notSubmitted")}. ${t("draft.queued")}. ${t("draft.pending")}. ${t("draft.confirmed")}.`} />}
      />

      <Card className="mb-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="section-title">Connection simulation</h2>
            <p className="text-sm text-muted">
              This toggle simulates the network. It does not contact any government system.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              role="switch"
              aria-checked={online}
              onClick={() => setOnline((value) => !value)}
              className={cn(
                "inline-flex min-h-11 items-center gap-2 rounded-xl border px-4 text-sm font-semibold",
                online ? "border-brand-300 bg-brand-50 text-brand-950" : "border-amber-300 bg-warningBg text-amber-950",
              )}
            >
              {online ? <Wifi aria-hidden="true" className="size-4" /> : <WifiOff aria-hidden="true" className="size-4" />}
              {online ? "Network online" : "Network offline"}
            </button>
            <label className="flex min-h-11 items-center gap-2 rounded-xl border border-line px-3 text-sm">
              <input
                type="checkbox"
                className="size-4 accent-brand-800"
                checked={simulateReceipt}
                onChange={(event) => setSimulateReceipt(event.target.checked)}
              />
              Use simulated test adapter
            </label>
          </div>
        </div>
        <Notice tone="warning" className="mt-3" title="What reconnection means">
          Syncing sends draft data. It does not confirm official submission. Only a verified acknowledgement from the
          configured adapter is shown as confirmed, and this demo's adapter is simulated.
        </Notice>
      </Card>

      {loading ? <LoadingState /> : null}
      {error ? <ErrorState message={error} onRetry={load} /> : null}
      {notice ? <Notice tone="info" className="mb-4" ariaLive="polite">{notice}</Notice> : null}

      <div className="space-y-4">
        {drafts.map((draft) => (
          <Card key={draft.id}>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <h2 className="text-lg font-bold">{draft.draft_ref}</h2>
                  <TranslatedDraftBadge state={draft.state} />
                  <span className="chip border-slate-300 bg-unknownBg text-slate-700">{draft.kind.replaceAll("_", " ")}</span>
                </div>
                <p className="mt-1 text-sm font-medium text-ink">{draft.notice}</p>
                <p className="text-xs text-muted">
                  Local draft reference — never an official receipt. Version {draft.version} ·{" "}
                  {new Date(draft.updated_at).toLocaleString()}
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                <Button
                  variant="secondary"
                  className="min-h-9 px-3 py-1.5 text-xs"
                  onClick={() => run(draft, "sync")}
                  disabled={busyId === draft.id || draft.state === "SUBMITTED_CONFIRMED"}
                >
                  {online ? <RefreshCw aria-hidden="true" className="size-4" /> : <CloudOff aria-hidden="true" className="size-4" />}
                  {online ? "Sync draft" : "Queue offline"}
                </Button>
                <Button
                  variant="secondary"
                  className="min-h-9 px-3 py-1.5 text-xs"
                  onClick={() => run(draft, "verify")}
                  disabled={busyId === draft.id || draft.state !== "SUBMISSION_PENDING_VERIFICATION"}
                >
                  <ShieldCheck aria-hidden="true" className="size-4" />
                  Check acknowledgement
                </Button>
                <Button
                  variant="ghost"
                  className="min-h-9 px-3 py-1.5 text-xs"
                  onClick={() => run(draft, "cancel")}
                  disabled={busyId === draft.id || draft.state === "SUBMITTED_CONFIRMED"}
                >
                  <Trash2 aria-hidden="true" className="size-4" />
                  Clear
                </Button>
              </div>
            </div>

            <div className="mt-3 grid gap-3 sm:grid-cols-2">
              <div className="rounded-xl border border-line p-3">
                <p className="text-xs font-bold uppercase tracking-wide text-muted">Draft content</p>
                <pre className="mt-1 max-h-40 overflow-auto whitespace-pre-wrap text-xs text-ink">
                  {JSON.stringify(draft.payload, null, 2)}
                </pre>
              </div>
              <div>
                <dl>
                  <DataRow label="Local draft reference">{draft.draft_ref}</DataRow>
                  <DataRow label="Official receipt">
                    {draft.receipt?.receipt_number ? (
                      <span>
                        {draft.receipt.receipt_number}{" "}
                        <span className="chip ml-1 border-amber-300 bg-warningBg text-amber-950">SIMULATED</span>
                      </span>
                    ) : (
                      "None verified"
                    )}
                  </DataRow>
                  <DataRow label="Submission status">
                    {draft.state === "SUBMITTED_CONFIRMED" ? "Confirmed by configured adapter" : t("common.notVerified")}
                  </DataRow>
                </dl>
                {draft.receipt?.message ? (
                  <p className="mt-2 rounded-lg bg-warningBg p-2 text-xs font-semibold text-amber-950">
                    {draft.receipt.message}
                  </p>
                ) : null}
                {draft.last_error ? <p className="mt-2 text-xs text-danger">{draft.last_error}</p> : null}
              </div>
            </div>
          </Card>
        ))}
        {!loading && drafts.length === 0 ? (
          <Notice tone="info">
            No drafts are visible in this session. Draft creation is available from the correction simulator.
          </Notice>
        ) : null}
      </div>

      <Card className="mt-4">
        <h2 className="section-title">Draft state model</h2>
        <p className="text-sm text-muted">No generic "pending" label is used. Each state has its own meaning.</p>
        <ul className="mt-3 grid gap-2 sm:grid-cols-2">
          {ALL_STATES.map((state) => (
            <li key={state} className="flex flex-wrap items-center gap-2 rounded-lg border border-line p-2.5">
              <TranslatedDraftBadge state={state} />
              <span className="text-xs text-muted">{state}</span>
            </li>
          ))}
        </ul>
        <div className="mt-3 flex flex-wrap gap-4 text-xs text-muted">
          <span className="inline-flex items-center gap-1">
            <Cloud aria-hidden="true" className="size-4" /> Sync ≠ submission
          </span>
          <span className="inline-flex items-center gap-1">
            <ShieldCheck aria-hidden="true" className="size-4" /> Receipt requires verification
          </span>
          <span className="inline-flex items-center gap-1">
            <WifiOff aria-hidden="true" className="size-4" /> Offline queue is explicit
          </span>
        </div>
      </Card>
    </div>
  );
}
