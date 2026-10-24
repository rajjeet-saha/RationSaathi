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
        if (!cancelled) setError(err instanceof ApiError ? err.message : t("overview.loadError"));
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
      <Notice tone="warning" title={t("overview.facilitatorConsentTitle")}>
        {t("overview.facilitatorConsentBody")}
      </Notice>
    );
  }

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={() => window.location.reload()} />;
  if (!household) return <ErrorState message={t("overview.householdUnavailable")} />;

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
        title={t("overview.todayTitle", { alias: member.alias })}
        description={
          <span>
            {t("sessionPrivacy")} {t("overview.membersExist", { count: household.member_count })}
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

      <ReadAloud text={readback} label={t("overview.readAloud")} />

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <Card>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h2 className="section-title">{t("portability.whatCanIDo")}</h2>
            <ProvenanceBadge provenance={household.provenance as Household["provenance"] as never} label={household.provenance_label} />
          </div>
          <p className="mt-1 text-sm text-muted">{t("overview.answerDepends")}</p>

          <div className="mt-4 space-y-3">
            {[
              { decision: rice, commodity: t("overview.rice") },
              { decision: wheat, commodity: t("overview.wheat") },
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
                        {decision.stock.age_hours != null
                          ? t("overview.updatedAgo", { hours: decision.stock.age_hours })
                          : t("overview.unknown")}{" "}
                        · {decision.stock.source}
                      </span>
                    </div>
                  ) : null}
                  <Button variant="ghost" className="mt-2 min-h-9 px-2 py-1 text-xs" onClick={() => navigate("/migration")}>
                    {t("overview.seeOptions")}
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
                <h2 className="section-title">{t("overview.mismatchTitle")}</h2>
                <p className="mt-1 text-sm leading-relaxed text-muted">
                  Household record: <strong>{member.full_name}</strong>, age {member.age ?? t("overview.unknown")}.
                  Identity-document reference: <strong>{member.document.name ?? "not recorded"}</strong>, age{" "}
                  {member.document.age ?? t("overview.unknown")}.
                </p>
                <p className="mt-1 text-xs text-muted">{t("overview.mismatchEvidence")}</p>
                <Button variant="secondary" className="mt-3" onClick={() => navigate("/corrections")}>
                  {t("overview.reviewSafely")}
                  <ArrowRight aria-hidden="true" className="size-4" />
                </Button>
              </div>
            </div>
          </Card>

          <Card>
            <div className="flex items-center gap-2">
              <CalendarClock aria-hidden="true" className="size-5 text-brand-800" />
              <h2 className="section-title">{t("overview.grievanceStatus")}</h2>
            </div>
            {oldGrievance ? (
              <div className="mt-3 rounded-xl border border-line p-3">
                <p className="text-sm font-semibold">{oldGrievance.subject}</p>
                <p className="mt-1 text-xs text-muted">
                  {t("overview.filedDaysAgo", { days: oldGrievance.deadline.filed_days_ago ?? 0 })} · {oldGrievance.status} ·{" "}
                  receipt {oldGrievance.official_receipt_number ?? t("overview.receiptNotVerified")}
                </p>
                <Notice tone="warning" className="mt-2" title={t("overview.deadlineNotVerified")}>
                  {t("grievance.deadlineUnknown")} {t("overview.elapsedNote")}
                </Notice>
                <Button
                  variant="secondary"
                  className="mt-2"
                  onClick={() => navigate(`/grievances/${oldGrievance.id}`)}
                >
                  {t("overview.openGrievance")}
                </Button>
              </div>
            ) : (
              <p className="mt-2 text-sm text-muted">
                {t("overview.noVerifiedDeadline", { count: deadlineUnknown.length })}{" "}
                <Link className="link" to="/grievances">
                  {t("overview.viewGrievances")}
                </Link>
              </p>
            )}
          </Card>

          <Card>
            <div className="flex items-center gap-2">
              <ClipboardList aria-hidden="true" className="size-5 text-brand-800" />
              <h2 className="section-title">{t("overview.draftsWaiting")}</h2>
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
              <p className="mt-2 text-sm text-muted">{t("overview.noDrafts")}</p>
            )}
            <Button variant="secondary" className="mt-3" onClick={() => navigate("/drafts")}>
              {t("overview.openDrafts")}
            </Button>
          </Card>
        </div>
      </div>

      <Card className="mt-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h2 className="section-title">{t("overview.whoResponsible")}</h2>
            <p className="text-sm text-muted">{t("overview.whoResponsibleBody")}</p>
          </div>
          <ShieldCheck aria-hidden="true" className="size-5 text-brand-800" />
        </div>
        <ul className="mt-3 grid gap-2 sm:grid-cols-2">
          {(rice?.authority_to_contact ?? [t("overview.defaultAuthority")]).map((authority) => (
            <li key={authority} className="rounded-xl border border-line bg-canvas/60 p-3 text-sm">
              {authority}
            </li>
          ))}
          <li className="rounded-xl border border-line bg-canvas/60 p-3 text-sm">{t("overview.needsVerification")}</li>
        </ul>
      </Card>

      <div className="mt-4">
        <HelpfulPictograms
          items={[
            {
              name: "mismatch",
              label: t("overview.mismatchTitle"),
              text: t("overview.pictoMismatch"),
            },
            {
              name: "draft",
              label: t("nav.drafts"),
              text: t("overview.pictoDraft"),
            },
            {
              name: "receipt",
              label: t("status.verified"),
              text: t("overview.pictoReceipt"),
            },
            {
              name: "privacy",
              label: t("privacy.title"),
              text: t("overview.pictoPrivacy"),
            },
          ]}
        />
      </div>
    </div>
  );
}
