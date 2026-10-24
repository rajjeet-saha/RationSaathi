import {
  ArrowRight,
  Ban,
  FileCheck2,
  FileWarning,
  Save,
  ShieldAlert,
  TriangleAlert
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useSession } from "../../app/session";
import { ReadAloud } from "../../components/ReadAloud";
import { RiskBadge } from "../../components/status";
import { Button, Card, DataRow, ErrorState, Field, LoadingState, Notice, PageHeader, cn } from "../../components/ui";
import { api, ApiError } from "../../lib/api";
import { useI18n } from "../../lib/i18n";
import type { Household, Simulation } from "../../lib/types";

const EVIDENCE_OPTIONS = [
  { id: "identity_reference", label: "Synthetic identity reference" },
  { id: "household_reference", label: "Synthetic household reference" },
  { id: "member_confirmation", label: "Household member confirms the values" },
  { id: "household_authority", label: "Proof of authority for a membership change" },
  { id: "authorised_office_confirmation", label: "Authorised-office reconciliation note" },
];

type Operation = "UPDATE_FIELD" | "DELETE_MEMBER" | "REPLACE_MEMBER" | "CREATE_MEMBER";

export function CorrectionsPage() {
  const { session } = useSession();
  const { t } = useI18n();
  const [household, setHousehold] = useState<Household | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [operation, setOperation] = useState<Operation>("UPDATE_FIELD");
  const [name, setName] = useState("");
  const [age, setAge] = useState("");
  const [evidence, setEvidence] = useState<string[]>(["identity_reference", "household_reference", "member_confirmation"]);
  const [simulation, setSimulation] = useState<Simulation | null>(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [saveResult, setSaveResult] = useState("");
  const [submitResult, setSubmitResult] = useState("");

  useEffect(() => {
    let cancelled = false;
    api
      .household()
      .then((payload) => {
        if (cancelled) return;
        setHousehold(payload);
        setName(payload.current_member.document.name ?? payload.current_member.full_name);
        setAge(String(payload.current_member.document.age ?? payload.current_member.age ?? ""));
      })
      .catch((err) => !cancelled && setError(err instanceof ApiError ? err.message : "Could not load the record."))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, []);

  const member = household?.current_member;
  const mismatch = member?.verification_state === "MISMATCH_FLAGGED";

  const evidenceChecklist = useMemo(() => {
    if (simulation) return simulation.evidence;
    return EVIDENCE_OPTIONS.map((item) => ({ ...item, required: true, provided: evidence.includes(item.id) }));
  }, [simulation, evidence]);

  const simulate = async (nextOperation: Operation = operation, fields?: { name?: string; age?: string }) => {
    if (!member) return;
    setBusy(true);
    setError("");
    setSaveResult("");
    setSubmitResult("");
    try {
      const payload = await api.simulateCorrection({
        operation: nextOperation,
        member_id: member.id,
        fields:
          nextOperation === "UPDATE_FIELD"
            ? {
                name: fields?.name ?? name,
                age: fields?.age ?? age ? Number(fields?.age ?? age) : null,
              }
            : {},
        evidence,
        reason: "Demo correction proposal prepared in the safety simulator.",
      });
      setSimulation(payload);
      setOperation(nextOperation);
      setNotice("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "The simulation could not be completed.");
    } finally {
      setBusy(false);
    }
  };

  const simulateDangerousReplace = () => simulate("REPLACE_MEMBER");
  const simulateDelete = () => simulate("DELETE_MEMBER");

  const saveDraft = async () => {
    if (!simulation) return;
    setBusy(true);
    setError("");
    try {
      const result = await api.saveCorrectionDraft(simulation.proposal_id, { evidence, note: "Prepared from the simulator." });
      setSaveResult(`Saved ${result.draft_ref} as ${result.state.replaceAll("_", " ").toLowerCase()} — not submitted.`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "The draft could not be saved.");
    } finally {
      setBusy(false);
    }
  };

  const attemptSubmit = async () => {
    if (!simulation) return;
    setBusy(true);
    setError("");
    setSubmitResult("");
    try {
      const result = await api.submitCorrection(simulation.proposal_id);
      setSubmitResult(JSON.stringify(result, null, 2));
    } catch (err) {
      setError(err instanceof ApiError ? `${err.status}: ${err.message}` : "The submission could not be completed.");
    } finally {
      setBusy(false);
    }
  };

  const toggleEvidence = (id: string) => {
    setEvidence((current) => (current.includes(id) ? current.filter((value) => value !== id) : [...current, id]));
  };

  if (loading) return <LoadingState />;
  if (error && !simulation) return <ErrorState message={error} onRetry={() => window.location.reload()} />;
  if (!member) return <ErrorState message="Member record not available." />;

  const readback = simulation
    ? `Member ${member.alias}. Proposed operation ${simulation.operation.replaceAll("_", " ")}. Risk ${simulation.risk_level.replaceAll("_", " ")}. ${simulation.blocked ? "The change is blocked. The original record is preserved." : "No destructive change was detected."} ${simulation.summary.join(" ")}`
    : `Member ${member.alias}. Household record ${member.full_name}, age ${member.age}. Document ${member.document.name}, age ${member.document.age}. ${t("correction.readback")}`;

  return (
    <div>
      <PageHeader
        eyebrow="Safe record correction"
        title="Compare before you change anything"
        description="The simulator predicts membership and entitlement impact before any official process. Destructive proposals are blocked server-side, not just hidden in the UI."
        icon={<FileWarning aria-hidden="true" className="size-5" />}
        actions={<ReadAloud compact text={readback} />}
      />

      {mismatch ? (
        <Notice tone="warning" className="mb-4" title="Mismatched member record">
          <p>
            Household record: <strong>{member.full_name}</strong>, age {member.age}. Identity reference:{" "}
            <strong>{member.document.name}</strong>, age {member.document.age}.
          </p>
          <p>Evidence may itself be incorrect; the simulator does not assume which value is right.</p>
        </Notice>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-[1fr_1.15fr]">
        <Card>
          <h2 className="section-title">Proposed correction</h2>
          <p className="mt-1 text-sm text-muted">
            Select the synthetic member, describe the change, attach only the necessary evidence, then run the simulator.
          </p>

          <div className="mt-3 rounded-xl border border-line p-3">
            <p className="text-xs font-bold uppercase tracking-wide text-muted">Selected member</p>
            <p className="text-sm font-semibold">
              {member.alias} — {member.full_name}, age {member.age}
            </p>
            <p className="text-xs text-muted">Only this member's values are shown in this session.</p>
          </div>

          <div className="mt-3">
            <label className="label" htmlFor="operation">
              Operation
            </label>
            <select
              id="operation"
              className="field"
              value={operation}
              onChange={(event) => setOperation(event.target.value as Operation)}
            >
              <option value="UPDATE_FIELD">Update name / age (preserves member)</option>
              <option value="REPLACE_MEMBER">Replace member record (destructive demo)</option>
              <option value="DELETE_MEMBER">Delete member (destructive demo)</option>
              <option value="CREATE_MEMBER">Create a new member (duplicate test)</option>
            </select>
          </div>

          {operation === "UPDATE_FIELD" ? (
            <div className="mt-3 grid gap-3 sm:grid-cols-2">
              <Field label="Proposed name" htmlFor="proposed-name">
                <input id="proposed-name" className="field" value={name} onChange={(event) => setName(event.target.value)} />
              </Field>
              <Field label="Proposed age" htmlFor="proposed-age">
                <input
                  id="proposed-age"
                  className="field"
                  inputMode="numeric"
                  value={age}
                  onChange={(event) => setAge(event.target.value)}
                />
              </Field>
            </div>
          ) : null}

          <fieldset className="mt-3">
            <legend className="label">Evidence checklist</legend>
            <div className="space-y-2">
              {EVIDENCE_OPTIONS.map((item) => (
                <label key={item.id} className="flex min-h-11 items-start gap-2 rounded-lg border border-line p-2.5 text-sm">
                  <input
                    type="checkbox"
                    className="mt-1 size-4 accent-brand-800"
                    checked={evidence.includes(item.id)}
                    onChange={() => toggleEvidence(item.id)}
                  />
                  <span>{item.label}</span>
                </label>
              ))}
            </div>
          </fieldset>

          <div className="mt-4 flex flex-wrap gap-2">
            <Button onClick={() => simulate()} disabled={busy}>
              <FileCheck2 aria-hidden="true" className="size-4" />
              {busy ? "Simulating…" : "Run safe simulation"}
            </Button>
            <Button variant="secondary" onClick={() => simulate("UPDATE_FIELD", { name: member.document.name ?? member.full_name, age: String(member.document.age ?? member.age ?? "") })} disabled={busy}>
              Use document values
            </Button>
          </div>

          <div className="mt-4 rounded-xl border border-red-200 bg-red-50/60 p-3">
            <p className="flex items-center gap-2 text-sm font-bold text-red-950">
              <ShieldAlert aria-hidden="true" className="size-4" />
              Dangerous demo actions
            </p>
            <p className="mt-1 text-xs leading-relaxed text-red-900">
              These mimic an unsafe form that deletes and recreates a member. They must be blocked before submission and
              are preserved only as blocked simulation records.
            </p>
            <div className="mt-2 flex flex-wrap gap-2">
              <Button variant="danger" className="min-h-9 px-3 py-1.5 text-xs" onClick={simulateDangerousReplace} disabled={busy}>
                <Ban aria-hidden="true" className="size-4" />
                Try replace and delete
              </Button>
              <Button variant="danger" className="min-h-9 px-3 py-1.5 text-xs" onClick={simulateDelete} disabled={busy}>
                Try deleting this member
              </Button>
            </div>
          </div>

          {error ? <Notice tone="danger" className="mt-3">{error}</Notice> : null}
        </Card>

        <div className="space-y-4">
          {!simulation ? (
            <Card>
              <h2 className="section-title">Before-and-after preview</h2>
              <p className="mt-2 text-sm text-muted">
                Run the simulator to see member counts, entitlement links, draw history and every risk finding. Nothing is
                changed until an authorised process verifies it.
              </p>
              <ul className="mt-3 space-y-2 text-sm text-muted">
                <li>• Destructive changes are blocked, not merely warned about.</li>
                <li>• Uncertain changes require human review.</li>
                <li>• A saved draft is explicitly not an official submission.</li>
              </ul>
            </Card>
          ) : (
            <>
              <Card
                className={cn(
                  "border-2",
                  simulation.blocked
                    ? "border-red-400 bg-red-50/40"
                    : simulation.requires_review
                      ? "border-amber-300 bg-amber-50/40"
                      : "border-brand-300",
                )}
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <h2 className="section-title flex items-center gap-2">
                    <TriangleAlert aria-hidden="true" className="size-5" />
                    {simulation.blocked
                      ? t("correction.blockedTitle")
                      : simulation.requires_review
                        ? t("correction.reviewTitle")
                        : t("correction.safeTitle")}
                  </h2>
                  <RiskBadge level={simulation.risk_level} />
                </div>
                <p className="mt-2 text-sm font-semibold text-ink">{simulation.recommended_action}</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {simulation.blocked ? (
                    <Notice tone="danger" className="w-full" title="Original record preserved">
                      {t("correction.originalPreserved")} {t("correction.cannotSubmit")}
                    </Notice>
                  ) : null}
                  <ReadAloud text={readback} label="Read the risk decision" />
                </div>
              </Card>

              <Card>
                <h2 className="section-title">Before and after</h2>
                <div className="mt-3 grid gap-3 sm:grid-cols-2">
                  <div className="rounded-xl border border-line p-3">
                    <p className="text-xs font-bold uppercase tracking-wide text-muted">{t("correction.before")}</p>
                    <p className="mt-1 text-2xl font-bold">{simulation.diff.member_count_before}</p>
                    <p className="text-xs text-muted">members · {simulation.diff.entitlement_links_before} entitlement links</p>
                  </div>
                  <div className="rounded-xl border border-line p-3">
                    <p className="text-xs font-bold uppercase tracking-wide text-muted">{t("correction.after")}</p>
                    <p className="mt-1 text-2xl font-bold">{simulation.diff.member_count_after}</p>
                    <p className="text-xs text-muted">members · {simulation.diff.entitlement_links_after} entitlement links</p>
                  </div>
                </div>

                <dl className="mt-3">
                  <DataRow label="Operation">{simulation.operation.replaceAll("_", " ")}</DataRow>
                  <DataRow label="Members removed">{simulation.diff.members_removed.length}</DataRow>
                  <DataRow label="Members added">{simulation.diff.members_added.length}</DataRow>
                  <DataRow label="Entitlement links removed">
                    {simulation.diff.entitlement_links_removed.length}
                  </DataRow>
                  <DataRow label="Periods affected">
                    {simulation.diff.entitlement_periods_affected.join(", ") || "None"}
                  </DataRow>
                  <DataRow label="Draw-history links affected">
                    {simulation.diff.draw_history_links_affected.length}
                  </DataRow>
                  <DataRow label="Unresolved identity conflicts">
                    {simulation.diff.unresolved_identity_conflicts.length || "None"}
                  </DataRow>
                </dl>

                <h3 className="mt-4 text-sm font-bold uppercase tracking-wide text-muted">Risk findings</h3>
                <ul className="mt-2 space-y-2">
                  {simulation.findings.map((finding, index) => (
                    <li
                      key={`${finding.code}-${index}`}
                      className={cn(
                        "rounded-xl border p-3 text-sm",
                        finding.severity === "BLOCKED" || finding.severity === "HIGH"
                          ? "border-red-300 bg-dangerBg/60"
                          : finding.severity === "REVIEW_REQUIRED"
                            ? "border-amber-300 bg-warningBg/60"
                            : "border-line",
                      )}
                    >
                      <div className="flex flex-wrap items-center gap-2">
                        <RiskBadge level={finding.severity} />
                        <span className="text-xs text-muted">{finding.code}</span>
                      </div>
                      <p className="mt-1">{finding.message}</p>
                    </li>
                  ))}
                </ul>
              </Card>

              <Card>
                <h2 className="section-title">Evidence checklist</h2>
                <ul className="mt-2 space-y-2">
                  {evidenceChecklist.map((item) => (
                    <li key={item.id} className="flex items-center justify-between gap-2 rounded-lg border border-line p-2.5 text-sm">
                      <span>{item.label}</span>
                      <span className={cn("chip", item.provided ? "border-brand-300 bg-brand-50 text-brand-950" : "border-amber-300 bg-warningBg text-amber-950")}>
                        {item.provided ? "Provided" : "Missing"}
                      </span>
                    </li>
                  ))}
                </ul>

                <div className="mt-4 flex flex-wrap gap-2">
                  <Button variant="secondary" onClick={saveDraft} disabled={busy || simulation.blocked}>
                    <Save aria-hidden="true" className="size-4" />
                    {t("correction.saveDraft")}
                  </Button>
                  <Button variant="ghost" onClick={attemptSubmit} disabled={busy || simulation.blocked}>
                    Demo test: attempt submission
                    <ArrowRight aria-hidden="true" className="size-4" />
                  </Button>
                </div>
                {simulation.blocked ? (
                  <p className="mt-2 text-xs font-semibold text-danger">
                    Blocked proposals cannot be saved for submission or sent. The simulated record remains unchanged.
                  </p>
                ) : null}
                {saveResult ? <Notice tone="success" className="mt-3" ariaLive="polite">{saveResult}</Notice> : null}
                {submitResult ? (
                  <Notice tone="success" className="mt-3" title="Simulated adapter response">
                    <pre className="max-h-52 overflow-auto whitespace-pre-wrap text-xs">{submitResult}</pre>
                  </Notice>
                ) : null}
                <p className="mt-2 text-xs text-muted">
                  A submission, if permitted, uses the labelled simulated adapter. Its receipt is not a government receipt.
                </p>
              </Card>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
