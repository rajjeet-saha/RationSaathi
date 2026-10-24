import { Bus, Clock3, Globe2, MapPin, ShieldQuestion } from "lucide-react";
import { useEffect, useState } from "react";
import { useSession } from "../../app/session";
import { ReadAloud } from "../../components/ReadAloud";
import { HelpfulPictograms } from "../../components/Pictogram";
import { DecisionBadge, StockBadge } from "../../components/status";
import { Button, Card, ErrorState, LoadingState, Notice, PageHeader, cn } from "../../components/ui";
import { api, ApiError } from "../../lib/api";
import { useI18n } from "../../lib/i18n";
import type { Decision, Household } from "../../lib/types";

const COMMODITIES = [
  { code: "RICE", label: "Rice" },
  { code: "WHEAT", label: "Wheat flour" },
  { code: "SUGAR", label: "Sugar" },
  { code: "KEROSENE", label: "Kerosene" },
];

interface StockPayload {
  shop: { id: string; name: string; address_label: string };
  commodities: {
    commodity_code: string;
    state: string;
    state_label: string;
    observed_at: string;
    source: string;
    provenance: string;
    provenance_label: string;
    note: string | null;
  }[];
  notice: string;
}

export function MigrationPage() {
  const { session } = useSession();
  const { t } = useI18n();
  const [household, setHousehold] = useState<Household | null>(null);
  const [commodity, setCommodity] = useState("RICE");
  const [decision, setDecision] = useState<Decision | null>(null);
  const [stock, setStock] = useState<StockPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const memberId = session?.member?.id;

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    api
      .household()
      .then(async (payload) => {
        if (cancelled) return;
        setHousehold(payload);
        if (payload.destination_shop_id) {
          const stockPayload = (await api.stockStatus(payload.destination_shop_id)) as unknown as StockPayload;
          if (!cancelled) setStock(stockPayload);
        }
      })
      .catch((err) => !cancelled && setError(err instanceof ApiError ? err.message : "Could not load migration data."))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!memberId) return;
    let cancelled = false;
    setError("");
    api
      .evaluatePortability(memberId, commodity)
      .then((payload) => !cancelled && setDecision(payload))
      .catch((err) => !cancelled && setError(err instanceof ApiError ? err.message : "Could not evaluate this pathway."));
    return () => {
      cancelled = true;
    };
  }, [memberId, commodity]);

  if (!session?.member) {
    return <Notice tone="warning">Record consent for the member profile before using the migration navigator.</Notice>;
  }
  if (loading && !household) return <LoadingState />;
  if (error && !decision) return <ErrorState message={error} onRetry={() => window.location.reload()} />;

  const readback = decision
    ? `${decision.headline}. ${decision.reasons.join(" ")} ${t("portability.travelWarning")} ${t("portability.noGuarantee")}`
    : "Evaluating migration options.";

  return (
    <div>
      <PageHeader
        eyebrow="Migration and portability"
        title={t("portability.whatCanIDo")}
        description={
          <span>
            {household ? `${household.home_state} → ${household.destination_state}` : "State pair"} · configured rules
            version {decision?.rule.version ?? "…"}. Synthetic rules only; this is not a statement of law.
          </span>
        }
        icon={<Globe2 aria-hidden="true" className="size-5" />}
      />

      <div className="mb-4 flex flex-wrap gap-2" role="group" aria-label="Choose commodity">
        {COMMODITIES.map((item) => (
          <button
            key={item.code}
            type="button"
            aria-pressed={commodity === item.code}
            onClick={() => setCommodity(item.code)}
            className={cn(
              "min-h-11 rounded-xl border px-4 text-sm font-semibold",
              commodity === item.code
                ? "border-brand-800 bg-brand-800 text-white"
                : "border-line bg-white text-ink hover:bg-brand-50",
            )}
          >
            {item.label}
          </button>
        ))}
      </div>

      {!decision ? (
        <LoadingState label="Evaluating the configured pathway…" />
      ) : (
        <div className="grid gap-4 lg:grid-cols-[1.25fr_1fr]">
          <div className="space-y-4">
            <Card>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h2 className="section-title">
                  {decision.commodity.name ?? commodity} at the destination shop
                </h2>
                <DecisionBadge decision={decision.decision} />
              </div>
              <p className="mt-3 text-lg font-semibold leading-snug text-brand-950">{decision.headline}</p>

              {decision.stock ? (
                <div className="mt-3 rounded-xl border border-line bg-canvas/50 p-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <StockBadge state={decision.stock.state} label={decision.stock.label} />
                    <span className="text-xs text-muted">
                      Last updated:{" "}
                      {decision.stock.observed_at
                        ? new Date(decision.stock.observed_at).toLocaleString()
                        : "No record"}{" "}
                      {decision.stock.age_hours != null ? `(${decision.stock.age_hours}h ago)` : ""}
                    </span>
                  </div>
                  <p className="mt-2 text-xs leading-relaxed text-muted">
                    Supplier: {decision.stock.source} · Provenance: {decision.stock.provenance}
                  </p>
                  {decision.stock.note ? <p className="mt-1 text-xs text-muted">{decision.stock.note}</p> : null}
                  {["STALE", "UNKNOWN", "SOURCE_UNAVAILABLE"].includes(decision.stock.state) ? (
                    <p className="mt-2 rounded-lg bg-warningBg px-2 py-1.5 text-xs font-semibold text-amber-950">
                      {t("portability.stockUncertain")} {t("portability.travelWarning")}
                    </p>
                  ) : null}
                </div>
              ) : null}

              <h3 className="mt-4 text-sm font-bold uppercase tracking-wide text-muted">Why</h3>
              <ul className="mt-1 space-y-1 text-sm leading-relaxed text-ink">
                {decision.reasons.map((reason) => (
                  <li key={reason}>• {reason}</li>
                ))}
              </ul>

              <h3 className="mt-4 text-sm font-bold uppercase tracking-wide text-muted">What this does not guarantee</h3>
              <ul className="mt-1 space-y-1 text-sm text-muted">
                {decision.cannot_guarantee.map((item) => (
                  <li key={item}>• {item}</li>
                ))}
              </ul>

              <ReadAloud text={readback} label="Read the decision aloud" />
            </Card>

            <Card>
              <h2 className="section-title">Alternative pathways</h2>
              <p className="mt-1 text-sm text-muted">
                No substitution, reimbursement, additional quantity or availability elsewhere is promised.
              </p>
              <ul className="mt-3 space-y-2">
                {decision.alternative_pathways.map((pathway) => (
                  <li key={pathway.id} className="rounded-xl border border-line p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <p className="text-sm font-semibold">{pathway.title}</p>
                      <span className="chip border-slate-300 bg-unknownBg text-slate-700">
                        <ShieldQuestion aria-hidden="true" className="size-3.5" />
                        Unverified
                      </span>
                    </div>
                    <p className="mt-1 text-sm text-muted">{pathway.detail}</p>
                  </li>
                ))}
              </ul>
            </Card>
          </div>

          <div className="space-y-4">
            <Card>
              <h2 className="section-title">Evidence needed</h2>
              <ul className="mt-2 space-y-2">
                {decision.evidence_status.map((item) => (
                  <li key={item.id} className="flex items-start justify-between gap-2 rounded-lg border border-line p-2.5 text-sm">
                    <span>
                      {item.label}
                      {item.note ? <span className="mt-0.5 block text-xs text-muted">{item.note}</span> : null}
                    </span>
                    <span
                      className={cn(
                        "chip shrink-0",
                        item.present
                          ? "border-brand-300 bg-brand-50 text-brand-950"
                          : "border-amber-300 bg-warningBg text-amber-950",
                      )}
                    >
                      {item.present ? "Recorded" : "Missing"}
                    </span>
                  </li>
                ))}
              </ul>
              <Notice tone="info" className="mt-3">
                Evidence requirements come from the synthetic rule for this state pair. An authorised office may ask for
                more.
              </Notice>
            </Card>

            <Card>
              <h2 className="section-title">Who to contact</h2>
              <ul className="mt-2 space-y-1.5 text-sm">
                {decision.authority_to_contact.map((authority) => (
                  <li key={authority} className="flex items-start gap-2">
                    <MapPin aria-hidden="true" className="mt-0.5 size-4 shrink-0 text-brand-800" />
                    {authority}
                  </li>
                ))}
              </ul>
              <p className="mt-3 text-xs text-muted">
                Destination shop: {decision.context.shop.name}
                {decision.context.shop.address_label ? ` — ${decision.context.shop.address_label}` : ""}
              </p>
            </Card>

            {stock ? (
              <Card>
                <h2 className="section-title">Shop stock board</h2>
                <p className="text-xs text-muted">{stock.notice}</p>
                <ul className="mt-2 space-y-2">
                  {stock.commodities.map((item) => (
                    <li key={item.commodity_code} className="rounded-lg border border-line p-2.5">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <p className="text-sm font-semibold">{item.commodity_code}</p>
                        <StockBadge state={item.state} label={item.state_label} />
                      </div>
                      <p className="mt-1 flex items-center gap-1 text-xs text-muted">
                        <Clock3 aria-hidden="true" className="size-3.5" />
                        {new Date(item.observed_at).toLocaleString()} · {item.provenance_label}
                      </p>
                    </li>
                  ))}
                </ul>
              </Card>
            ) : null}

            <Card>
              <h2 className="section-title">Rule source</h2>
              <p className="mt-1 text-sm text-ink">{decision.rule.source_label}</p>
              <p className="text-xs text-muted">
                Version {decision.rule.version} · evaluated {new Date(decision.context.evaluated_at).toLocaleString()}
              </p>
              <ul className="mt-2 space-y-1 text-xs text-muted">
                {(decision.rule.disclaimers ?? []).map((item) => (
                  <li key={item}>• {item}</li>
                ))}
              </ul>
            </Card>
          </div>
        </div>
      )}

      <div className="mt-4">
        <HelpfulPictograms
          items={[
            { name: "travel", text: "Travel only after the shop or office confirms today's availability." },
            { name: "outOfStock", text: "An out-of-stock report is not proof that no other lawful option exists." },
            { name: "available", text: "Only verified stock supports an 'eligible to proceed' answer." },
            { name: "missingDocument", text: "Missing evidence pauses the pathway; it does not remove eligibility." },
          ]}
        />
      </div>
      <p className="mt-4 flex items-center gap-2 text-xs text-muted">
        <Bus aria-hidden="true" className="size-4" />
        Return visits may be necessary. No travel reimbursement or alternative shop availability is promised.
      </p>
      {error ? <ErrorState message={error} /> : null}
    </div>
  );
}
