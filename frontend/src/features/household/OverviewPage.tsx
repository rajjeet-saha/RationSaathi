import {
  ArrowRight,
  CalendarClock,
  ChevronRight,
  ClipboardList,
  Globe2,
  ShieldCheck,
  TriangleAlert,
  UsersRound
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useSession } from "../../app/session";
import { ReadAloud } from "../../components/ReadAloud";
import { HelpfulPictograms } from "../../components/Pictogram";
import { DecisionBadge, ProvenanceBadge, StockBadge, TranslatedDraftBadge } from "../../components/status";
import { Button, Card, ErrorState, LoadingState, Notice, PageHeader } from "../../components/ui";
import { api, ApiError } from "../../lib/api";
import { useI18n } from "../../lib/i18n";
import type { Decision, Draft, Grievance, Household } from "../../lib/types";

export function OverviewPage() {
  const { session } = useSession();
  const { t } = useI18n();
  const navigate = useNavigate();
  const [household, setHousehold] = useState<Household | null>(null);
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [grievances, setGrievances] = useState<Grievance[]>([]);
  const [rice, setRice] = useState<Decision | null>(null);
  const [wheat, setWheat] = useState<Decision | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const memberId = session?.member?.id;

  useEffect(() => {
    if (!memberId) return;
    let cancelled = false;
    setLoading(true);
    setError("");
    Promise.all([
      api.household(),
      api.drafts(),
      api.grievances(),
      api.evaluatePortability(memberId, "RICE"),
      api.evaluatePortability(memberId, "WHEAT"),
    ])
      .then(([house, draftPayload, grievancePayload, riceDecision, wheatDecision]) => {
        if (cancelled) return;
        setHousehold(house);
        setDrafts(draftPayload.drafts);
        setGrievances(grievancePayload.grievances);
        setRice(riceDecision);
        setWheat(wheatDecision);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof ApiError ? err.message : "Could not load the household overview.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [memberId]);

  if (!session?.member) {
    return (
      <Notice tone="warning" title="Facilitator consent required">
        Open a member profile with recorded consent before using the household overview.
      </Notice>
    );
  }

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={() => window.location.reload()} />;
  if (!household) return <ErrorState message="Household not available." />;

  const member = household.current_member;
  const mismatch = member.verification_state === "MISMATCH_FLAGGED";
  const unsubmittedDrafts = drafts.filter((d) => d.state === "DRAFT_NOT_SUBMITTED" || d.state === "REQUIRES_REVIEW");
  const oldGrievance = grievances.find((g) => {
    if (!g.filed_at) return false;
    const days = Math.floor((Date.now() - new Date(g.filed_at).getTime()) / 86_400_000);
    return days >= 21 && !g.deadline.deadline_verified;
  });
  const deadlineUnknown = grievances.filter((g) => !g.deadline.deadline_verified);

  const readback = [
    `${t("appName")}. ${t("portability.whatCanIDo")}`,
    mismatch ? `${t("correction.reviewTitle")}. ${t("correction.originalPreserved")}` : "",
    rice ? rice.headline : "",
    oldGrievance ? `${t("grievance.deadlineUnknown")}. ${oldGrievance.subject}` : "",
    unsubmittedDrafts.length ? `${t("draft.notSubmitted")}.` : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div>
      <PageHeader
        eyebrow={`${household.reference} · ${household.home_state} → ${household.destination_state}`}
        title={`${member.alias} — today`}
        description={
          <span>
            {t("sessionPrivacy")} {household.member_count} household member records exist; only yours is loaded here.
          </span>
        }
        icon={<UsersRound aria-hidden="true" className="size-5" />}
        actions={
          <>
            <Button variant="secondary" onClick={() => navigate("/migration")}>
              <Globe2 aria-hidden="true" className="size-4" />
              {t("portability.whatCanIDo")}
            </Button>
            <Button onClick={() => navigate("/member")}>
              {t("nav.record")}
              <ArrowRight aria-hidden="true" className="size-4" />
            </Button>
          </>
        }
      />

      <ReadAloud text={readback} label="Read this page's safe next steps" />

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <Card>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h2 className="section-title">{t("portability.whatCanIDo")}</h2>
            <ProvenanceBadge provenance={household.provenance as Household["provenance"] as never} label={household.provenance_label} />
          </div>
          <p className="mt-1 text-sm text-muted">
            The answer depends on verified stock and entitlement data. Uncertainty is shown explicitly.
          </p>

          <div className="mt-4 space-y-3">
            {[
              { decision: rice, commodity: "Rice" },
              { decision: wheat, commodity: "Wheat flour" },
            ].map(({ decision, commodity }) =>
              decision ? (
                <div key={commodity} className="rounded-xl border border-line p-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="font-semibold">{commodity}</p>
                    <DecisionBadge decision={decision.decision} />
                  </div>
                  <p className="mt-2 text-sm leading-relaxed text-ink">{decision.headline}</p>
                  {decision.stock ? (
                    <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-muted">
                      <StockBadge state={decision.stock.state} label={decision.stock.label} />
                      <span>
                        Updated {decision.stock.age_hours != null ? `${decision.stock.age_hours}h ago` : "unknown"} ·{" "}
                        {decision.stock.source}
                      </span>
                    </div>
                  ) : null}
                  <Button variant="ghost" className="mt-2 min-h-9 px-2 py-1 text-xs" onClick={() => navigate("/migration")}>
                    See options and uncertainty
                    <ChevronRight aria-hidden="true" className="size-4" />
                  </Button>
                </div>
              ) : null,
            )}
          </div>
          <Notice tone="warning" className="mt-3">
            {t("portability.travelWarning")} {t("portability.noGuarantee")}
          </Notice>
        </Card>

        <div className="space-y-4">
          <Card className={mismatch ? "border-amber-300" : ""}>
            <div className="flex items-start gap-3">
              <span className="rounded-lg bg-warningBg p-2 text-warning">
                <TriangleAlert aria-hidden="true" className="size-5" />
              </span>
              <div>
                <h2 className="section-title">Record mismatch found</h2>
                <p className="mt-1 text-sm leading-relaxed text-muted">
                  Household record: <strong>{member.full_name}</strong>, age {member.age ?? "unknown"}.
                  Identity-document reference: <strong>{member.document.name ?? "not recorded"}</strong>, age{" "}
                  {member.document.age ?? "unknown"}.
                </p>
                <p className="mt-1 text-xs text-muted">
                  Evidence is not automatically assumed correct. A destructive correction is blocked before submission.
                </p>
                <Button variant="secondary" className="mt-3" onClick={() => navigate("/corrections")}>
                  Review safely
                  <ArrowRight aria-hidden="true" className="size-4" />
                </Button>
              </div>
            </div>
          </Card>

          <Card>
            <div className="flex items-center gap-2">
              <CalendarClock aria-hidden="true" className="size-5 text-brand-800" />
              <h2 className="section-title">Grievance status</h2>
            </div>
            {oldGrievance ? (
              <div className="mt-3 rounded-xl border border-line p-3">
                <p className="text-sm font-semibold">{oldGrievance.subject}</p>
                <p className="mt-1 text-xs text-muted">
                  Filed {oldGrievance.deadline.filed_days_ago} days ago · {oldGrievance.status} · receipt{" "}
                  {oldGrievance.official_receipt_number ?? "not verified"}
                </p>
                <Notice tone="warning" className="mt-2" title="Deadline not verified">
                  {t("grievance.deadlineUnknown")} Elapsed days alone do not prove a legal violation.
                </Notice>
                <Button
                  variant="secondary"
                  className="mt-2"
                  onClick={() => navigate(`/grievances/${oldGrievance.id}`)}
                >
                  Open grievance
                </Button>
              </div>
            ) : (
              <p className="mt-2 text-sm text-muted">
                {deadlineUnknown.length} grievance(s) have no verified deadline.{" "}
                <Link className="link" to="/grievances">
                  View grievances
                </Link>
              </p>
            )}
          </Card>

          <Card>
            <div className="flex items-center gap-2">
              <ClipboardList aria-hidden="true" className="size-5 text-brand-800" />
              <h2 className="section-title">Drafts waiting</h2>
            </div>
            {unsubmittedDrafts.length > 0 ? (
              <ul className="mt-2 space-y-2">
                {unsubmittedDrafts.map((draft) => (
                  <li key={draft.id} className="rounded-xl border border-amber-300 bg-warningBg/50 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <p className="text-sm font-semibold">{draft.draft_ref}</p>
                      <TranslatedDraftBadge state={draft.state} />
                    </div>
                    <p className="mt-1 text-xs text-muted">{draft.state_label}</p>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-2 text-sm text-muted">No unsubmitted drafts for this profile.</p>
            )}
            <Button variant="secondary" className="mt-3" onClick={() => navigate("/drafts")}>
              Open draft manager
            </Button>
          </Card>
        </div>
      </div>

      <Card className="mt-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h2 className="section-title">Who is responsible for the next step?</h2>
            <p className="text-sm text-muted">
              These contacts come from the configured demo rules; ownership still needs verification where stated.
            </p>
          </div>
          <ShieldCheck aria-hidden="true" className="size-5 text-brand-800" />
        </div>
        <ul className="mt-3 grid gap-2 sm:grid-cols-2">
          {(rice?.authority_to_contact ?? ["Destination-shop authorised office"]).map((authority) => (
            <li key={authority} className="rounded-xl border border-line bg-canvas/60 p-3 text-sm">
              {authority}
            </li>
          ))}
          <li className="rounded-xl border border-line bg-canvas/60 p-3 text-sm">
            Needs verification — confirm the responsible office from the receipt or receiving office.
          </li>
        </ul>
      </Card>

      <div className="mt-4">
        <HelpfulPictograms
          items={[
            {
              name: "mismatch",
              label: "Mismatch",
              text: "A difference in the record is flagged, not silently corrected.",
            },
            {
              name: "draft",
              label: "Draft",
              text: "A saved local draft is never an official submission.",
            },
            {
              name: "receipt",
              label: "Receipt verification",
              text: "Only a verified acknowledgement is shown as confirmed.",
            },
            {
              name: "privacy",
              label: "Privacy",
              text: "Only this member's records are visible in this session.",
            },
          ]}
        />
      </div>
    </div>
  );
}
