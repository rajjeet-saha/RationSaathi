import { ArrowLeft, CalendarClock, FileText, RefreshCw, Send, ShieldQuestion } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ReadAloud } from "../../components/ReadAloud";
import { Button, Card, DataRow, ErrorState, Field, LoadingState, Notice, PageHeader } from "../../components/ui";
import { api, ApiError } from "../../lib/api";
import { useI18n } from "../../lib/i18n";
import type { Escalation, Grievance } from "../../lib/types";

export function GrievanceDetailPage() {
  const { id = "" } = useParams();
  const { t } = useI18n();
  const [grievance, setGrievance] = useState<Grievance | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [office, setOffice] = useState("");
  const [officer, setOfficer] = useState("");
  const [contact, setContact] = useState("");
  const [escalation, setEscalation] = useState<Escalation | null>(null);
  const [body, setBody] = useState("");
  const [confirmChannel, setConfirmChannel] = useState(false);
  const [escalationState, setEscalationState] = useState("");

  const load = () => {
    setLoading(true);
    api
      .grievance(id)
      .then((payload) => {
        setGrievance(payload);
        setOffice(payload.responsible_office ?? "");
        setEscalationState(payload.escalations?.[0]?.state ?? "");
        if (payload.escalations?.[0]) {
          setBody(payload.escalations[0].body);
        }
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load the grievance."))
      .finally(() => setLoading(false));
  };

  useEffect(load, [id]);

  const verifyStatus = async () => {
    setBusy(true);
    setError("");
    try {
      const result = await api.verifyGrievance(id);
      setGrievance(result);
      setNotice(
        result.status === "OVERDUE"
          ? "Status recalculated. A configured deadline has passed with no qualifying response."
          : "Status checked against the configured policy.",
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not verify the status.");
    } finally {
      setBusy(false);
    }
  };

  const generate = async () => {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const result = await api.createEscalation(id, {
        recipient_office: office || undefined,
        officer_placeholder: officer || undefined,
        safe_contact: contact || undefined,
      });
      setEscalation(result);
      setBody(result.body);
      setEscalationState(result.state);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not generate the escalation draft.");
    } finally {
      setBusy(false);
    }
  };

  const saveDraft = async () => {
    if (!escalation) return;
    setBusy(true);
    try {
      const result = await api.updateEscalation(escalation.id, body);
      setEscalationState(result.state);
      setNotice("Escalation draft saved. It is still not submitted.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not save the escalation draft.");
    } finally {
      setBusy(false);
    }
  };

  const submit = async () => {
    if (!escalation) return;
    setBusy(true);
    setError("");
    try {
      const result = await api.submitEscalation(escalation.id, confirmChannel);
      setNotice(JSON.stringify(result, null, 2));
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? `${err.status}: ${err.message}` : "Could not submit the escalation.");
    } finally {
      setBusy(false);
    }
  };

  if (loading) return <LoadingState />;
  if (error && !grievance) return <ErrorState message={error} onRetry={load} />;
  if (!grievance) return null;

  const canSubmitEscalation = grievance.office_verified && Boolean(grievance.official_receipt_number);

  return (
    <div>
      <PageHeader
        eyebrow={`Grievance · ${grievance.category.replaceAll("_", " ")}`}
        title={grievance.subject}
        description={`Filed ${grievance.deadline.filed_days_ago ?? "?"} days ago · receipt ${grievance.official_receipt_number ?? "not verified"}.`}
        icon={<FileText aria-hidden="true" className="size-5" />}
        actions={
          <>
            <Link to="/grievances" className="btn-ghost gap-1 text-sm">
              <ArrowLeft aria-hidden="true" className="size-4" />
              All grievances
            </Link>
            <Button variant="secondary" onClick={verifyStatus} disabled={busy}>
              <RefreshCw aria-hidden="true" className="size-4" />
              Verify status
            </Button>
          </>
        }
      />

      {notice ? <Notice tone="info" className="mb-4" ariaLive="polite">{notice}</Notice> : null}
      {error ? <Notice tone="danger" className="mb-4">{error}</Notice> : null}

      <div className="grid gap-4 lg:grid-cols-[1fr_1.2fr]">
        <div className="space-y-4">
          <Card>
            <h2 className="section-title">Case record</h2>
            <dl className="mt-2">
              <DataRow label="Status">{grievance.status.replaceAll("_", " ")}</DataRow>
              <DataRow label="Filing date">
                {grievance.filed_at ? new Date(grievance.filed_at).toLocaleDateString() : "Unknown"}
              </DataRow>
              <DataRow label="Official receipt">{grievance.official_receipt_number ?? "Not verified"}</DataRow>
              <DataRow label="Provenance">
                {grievance.provenance.replaceAll("_", " ").toLowerCase()} (synthetic)
              </DataRow>
              <DataRow label="Ownership">
                {grievance.office_verified ? (
                  grievance.responsible_office
                ) : (
                  <span className="inline-flex items-start gap-1 text-warning">
                    <ShieldQuestion aria-hidden="true" className="mt-0.5 size-4" />
                    Needs verification
                  </span>
                )}
              </DataRow>
              <DataRow label="Assigned officer">{grievance.assigned_officer ?? "Not recorded"}</DataRow>
              <DataRow label="Response recorded">{grievance.response_recorded ? "Yes" : "No"}</DataRow>
            </dl>

            <div className="mt-3 rounded-xl border border-line p-3">
              <p className="flex items-center gap-2 text-sm font-bold">
                <CalendarClock aria-hidden="true" className="size-4" />
                Service deadline
              </p>
              {grievance.deadline.deadline_verified ? (
                <>
                  <p className="mt-1 text-sm">
                    {grievance.deadline.deadline_label} · policy {grievance.deadline.policy?.version}
                  </p>
                  <p className="mt-1 text-xs text-muted">{grievance.deadline.deadline_note}</p>
                  <p className="mt-1 text-xs text-muted">{grievance.deadline.policy?.source_label}</p>
                </>
              ) : (
                <p className="mt-1 text-sm font-semibold text-warning">{t("grievance.deadlineUnknown")}</p>
              )}
            </div>
            {grievance.response_summary ? (
              <Notice tone="success" className="mt-3" title="Recorded response">
                {grievance.response_summary}
              </Notice>
            ) : null}
          </Card>

          <Card>
            <h2 className="section-title">Case timeline</h2>
            <ol className="mt-2 space-y-3">
              {(grievance.events ?? []).map((event) => (
                <li key={`${event.event_type}-${event.occurred_at}`} className="border-l-2 border-brand-200 pl-3">
                  <p className="text-sm font-semibold">{event.event_type.replaceAll("_", " ")}</p>
                  <p className="text-xs text-muted">{new Date(event.occurred_at).toLocaleString()}</p>
                </li>
              ))}
              {(grievance.events ?? []).length === 0 ? <li className="text-sm text-muted">No events recorded.</li> : null}
            </ol>
          </Card>

          <ReadAloud
            text={`Grievance: ${grievance.subject}. Status ${grievance.status}. Filing date ${grievance.filed_at ? new Date(grievance.filed_at).toLocaleDateString() : "unknown"}. ${grievance.deadline.deadline_note}`}
            label="Read grievance status aloud"
          />
        </div>

        <div className="space-y-4">
          <Card>
            <h2 className="section-title">Escalation draft generator</h2>
            <p className="mt-1 text-sm text-muted">
              The letter uses placeholders where responsibility or a verified deadline is unknown. It never invents a law,
              receipt, officer name or address.
            </p>

            <div className="mt-3 grid gap-3 sm:grid-cols-2">
              <Field label="Responsible office" htmlFor="escalation-office" hint="Leave blank if not verified.">
                <input id="escalation-office" className="field" value={office} onChange={(event) => setOffice(event.target.value)} />
              </Field>
              <Field label="Officer placeholder" htmlFor="escalation-officer" optional>
                <input id="escalation-officer" className="field" value={officer} onChange={(event) => setOfficer(event.target.value)} />
              </Field>
            </div>
            <div className="mt-3">
              <Field
                label="Safe contact method"
                htmlFor="escalation-contact"
                hint="Do not use another member's private phone number without their consent."
              >
                <input
                  id="escalation-contact"
                  className="field"
                  value={contact}
                  onChange={(event) => setContact(event.target.value)}
                  placeholder="For example: facilitator centre reference"
                />
              </Field>
            </div>

            <div className="mt-3 flex flex-wrap gap-2">
              <Button onClick={generate} disabled={busy}>
                <FileText aria-hidden="true" className="size-4" />
                {escalation ? "Generate a new draft" : "Generate draft letter"}
              </Button>
            </div>

            {!canSubmitEscalation ? (
              <Notice tone="warning" className="mt-3" title="Escalation cannot be sent yet">
                <p>
                  The original receipt or responsible office is not verified. You can prepare and edit the draft, but the
                  backend will refuse to submit it until ownership is confirmed.
                </p>
              </Notice>
            ) : null}
          </Card>

          {escalation ? (
            <Card>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h2 className="section-title">Editable escalation letter</h2>
                <span className="chip border-amber-300 bg-warningBg text-amber-950">
                  {escalationState === "SUBMITTED_CONFIRMED" ? "SUBMITTED — SIMULATED" : "DRAFT — NOT SUBMITTED"}
                </span>
              </div>
              <label className="label mt-3" htmlFor="escalation-body">
                Letter body
              </label>
              <textarea
                id="escalation-body"
                className="field min-h-72 font-mono text-xs leading-relaxed"
                value={body}
                onChange={(event) => setBody(event.target.value)}
                disabled={escalationState === "SUBMITTED_CONFIRMED"}
              />
              <div className="mt-3 flex flex-wrap items-center gap-2">
                <Button variant="secondary" onClick={saveDraft} disabled={busy || escalationState === "SUBMITTED_CONFIRMED"}>
                  Save draft
                </Button>
                <Button onClick={submit} disabled={busy || !canSubmitEscalation || escalationState === "SUBMITTED_CONFIRMED"}>
                  <Send aria-hidden="true" className="size-4" />
                  Submit via simulated adapter
                </Button>
                <label className="flex min-h-11 items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    className="size-4 accent-brand-800"
                    checked={confirmChannel}
                    onChange={(event) => setConfirmChannel(event.target.checked)}
                  />
                  Confirm an authorised channel
                </label>
              </div>
              <p className="mt-2 text-xs text-muted">
                Submission is refused without a verified receipt, a verified office and explicit channel confirmation. The
                demo adapter's receipt is not a government receipt.
              </p>
            </Card>
          ) : null}
        </div>
      </div>
    </div>
  );
}
