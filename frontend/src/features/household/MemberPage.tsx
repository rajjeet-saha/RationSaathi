import { FileWarning, Lock, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useSession } from "../../app/session";
import { ReadAloud } from "../../components/ReadAloud";
import { ProvenanceBadge } from "../../components/status";
import { Button, Card, DataRow, ErrorState, LoadingState, Notice, PageHeader } from "../../components/ui";
import { api, ApiError } from "../../lib/api";
import { useI18n } from "../../lib/i18n";
import type { Household } from "../../lib/types";

export function MemberPage() {
  const { session } = useSession();
  const { t } = useI18n();
  const navigate = useNavigate();
  const [household, setHousehold] = useState<Household | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api
      .household()
      .then((payload) => !cancelled && setHousehold(payload))
      .catch((err) => !cancelled && setError(err instanceof ApiError ? err.message : "Could not load this profile."))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, []);

  if (!session?.member) {
    return <Notice tone="warning">Record consent before opening a member profile.</Notice>;
  }
  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={() => window.location.reload()} />;
  if (!household) return null;

  const member = household.current_member;
  const entitlements = household.own_entitlements;
  const mismatch =
    member.document.name &&
    (member.document.name !== member.full_name || member.document.age !== member.age);

  return (
    <div>
      <PageHeader
        eyebrow={`${household.reference} · profile scoped session`}
        title={member.alias}
        description="Member-level entitlements with source, verification and uncertainty. Quantities are synthetic test fixtures unless provenance says official."
        icon={<ShieldCheck aria-hidden="true" className="size-5" />}
        actions={
          <Button variant="secondary" onClick={() => navigate("/corrections")}>
            Review record mismatch
          </Button>
        }
      />

      <div className="grid gap-4 lg:grid-cols-[1.1fr_1fr]">
        <Card>
          <h2 className="section-title">Profile</h2>
          <dl className="mt-2">
            <DataRow label="Household record name">{member.full_name}</DataRow>
            <DataRow label="Age">{member.age ?? "Not recorded"}</DataRow>
            <DataRow label="Relationship">{member.relationship ?? "Not recorded"}</DataRow>
            <DataRow label="Membership status">{member.membership_status}</DataRow>
            <DataRow label="Verification state">{member.verification_state}</DataRow>
            <DataRow label="Consent">{member.consent_state}</DataRow>
            <DataRow label="Provenance">
              <ProvenanceBadge provenance={member.provenance} label={member.provenance_label} />
            </DataRow>
            <DataRow label="Absent head?">
              {member.is_head ? (member.is_absent ? "Head — currently absent" : "Head — present") : "No"}
            </DataRow>
            <DataRow label="Dependent">{member.is_dependent ? "Yes" : "No"}</DataRow>
          </dl>
        </Card>

        <Card>
          <h2 className="section-title">Identity-document comparison</h2>
          <p className="mt-1 text-sm text-muted">
            Synthetic reference only. Evidence may itself be wrong, so neither value is automatically treated as correct.
          </p>
          <dl className="mt-2">
            <DataRow label="Document name">{member.document.name ?? "Not recorded"}</DataRow>
            <DataRow label="Document age">{member.document.age ?? "Not recorded"}</DataRow>
            <DataRow label="Reference">
              {member.document.ref ? "Synthetic reference present" : "Missing"}
            </DataRow>
            <DataRow label="Document provenance">
              {member.document.provenance ? (
                <ProvenanceBadge provenance={member.document.provenance} label={member.document.provenance_label} />
              ) : (
                "Unknown"
              )}
            </DataRow>
          </dl>
          {mismatch ? (
            <Notice tone="warning" className="mt-3" title="Mismatch needs careful review">
              <p>
                The household record and identity reference differ. A correction cannot remove a member or entitlement
                link in this prototype.
              </p>
              <ReadAloud
                compact
                text={`${t("correction.readback")} Household name ${member.full_name}. Document name ${member.document.name}. Household age ${member.age}. Document age ${member.document.age}.`}
              />
            </Notice>
          ) : (
            <Notice tone="success" className="mt-3">
              No mismatch detected in the synthetic record.
            </Notice>
          )}
        </Card>
      </div>

      <Card className="mt-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h2 className="section-title">Per-commodity entitlements</h2>
            <p className="text-sm text-muted">{entitlements.length} synthetic entitlement record(s), current period.</p>
          </div>
          <span className="chip border-amber-300 bg-warningBg text-amber-950">
            <FileWarning aria-hidden="true" className="size-3.5" />
            Quantities are synthetic fixtures
          </span>
        </div>

        <div className="table-wrap mt-3">
          <table className="data-table">
            <caption className="sr-only">Member entitlements by commodity and period</caption>
            <thead>
              <tr>
                <th scope="col">Commodity</th>
                <th scope="col">Period</th>
                <th scope="col">Recorded values</th>
                <th scope="col">Remaining</th>
                <th scope="col">Source &amp; status</th>
              </tr>
            </thead>
            <tbody>
              {entitlements.map((entitlement) => (
                <tr key={entitlement.id}>
                  <td className="font-semibold">{entitlement.commodity_name}</td>
                  <td>{entitlement.period}</td>
                  <td>
                    <span className="block">
                      Entitled: {entitlement.entitled_qty ?? "unknown"} {entitlement.unit}
                    </span>
                    <span className="block text-xs text-muted">
                      Drawn: {entitlement.drawn_qty ?? "unknown"} {entitlement.unit}
                    </span>
                  </td>
                  <td>
                    <span className={entitlement.remaining.state === "UNABLE_TO_VERIFY" ? "font-semibold text-warning" : ""}>
                      {entitlement.remaining.state === "UNABLE_TO_VERIFY"
                        ? t("common.notVerified") + " — unable to verify remaining entitlement"
                        : entitlement.remaining.display}
                    </span>
                    <span className="mt-1 block text-xs text-muted">{entitlement.remaining.note}</span>
                  </td>
                  <td>
                    <div className="flex flex-col items-start gap-1">
                      <ProvenanceBadge provenance={entitlement.provenance} label={entitlement.provenance_label} />
                      <span className="text-xs text-muted">{entitlement.verification_status}</span>
                      <span className="text-xs text-muted">Rules {entitlement.rules_version}</span>
                    </div>
                  </td>
                </tr>
              ))}
              {entitlements.length === 0 ? (
                <tr>
                  <td colSpan={5}>No entitlement records are available for this member.</td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </Card>

      <Notice tone="info" className="mt-4" title="Privacy isolation">
        <p className="flex items-start gap-2">
          <Lock aria-hidden="true" className="mt-0.5 size-4 shrink-0" />
          {t("otherMembersHidden")} The backend rejects requests for another member's profile in this session. There is
          no household-wide endpoint that returns other members' entitlements.
        </p>
      </Notice>
    </div>
  );
}
