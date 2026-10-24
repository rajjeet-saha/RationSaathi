import { ArrowRight, Building2, Globe2, Languages, LogIn, ShieldCheck, UsersRound } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useSession } from "../../app/session";
import { DemoBanner } from "../../components/DemoBanner";
import { Button, Card, ErrorState, LoadingState, Notice, cn } from "../../components/ui";
import { api, ApiError } from "../../lib/api";
import { useI18n } from "../../lib/i18n";
import type { DemoHousehold } from "../../lib/types";

export function SignInPage() {
  const { signIn } = useSession();
  const { t, locale, setLocale } = useI18n();
  const navigate = useNavigate();
  const [households, setHouseholds] = useState<DemoHousehold[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const load = () => {
    setLoading(true);
    setError("");
    api
      .demoProfiles()
      .then((payload) => {
        setHouseholds(payload.households);
        setSelected((current) => current ?? payload.households[0]?.id ?? null);
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : t("signIn.loadError")))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const household = households.find((item) => item.id === selected) ?? null;

  const startMember = async (memberId: string) => {
    if (!household) return;
    setBusy(true);
    setError("");
    try {
      await signIn(household.id, "MEMBER", memberId);
      navigate("/", { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t("signIn.startError"));
    } finally {
      setBusy(false);
    }
  };

  const startFacilitator = async () => {
    if (!household) return;
    setBusy(true);
    setError("");
    try {
      await signIn(household.id, "FACILITATOR");
      navigate("/facilitator", { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t("signIn.assistedError"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen bg-canvas">
      <DemoBanner />
      <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-12">
        <div className="mb-8 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <svg viewBox="0 0 48 48" className="size-11" role="img" aria-label="RationSaathi logo">
              <rect width="48" height="48" rx="12" fill="#14532d" />
              <path d="M13 29c0-7 5-12 11-12s11 5 11 12" stroke="#dcefdf" strokeWidth="3" strokeLinecap="round" fill="none" />
              <path d="M24 17v15M17 32h14" stroke="#8cc99a" strokeWidth="3" strokeLinecap="round" />
              <circle cx="24" cy="13" r="2.6" fill="#fef3c7" />
            </svg>
            <div>
              <p className="text-2xl font-bold leading-tight text-brand-900">{t("appName")}</p>
              <p className="text-sm text-muted">{t("tagline")}</p>
            </div>
          </div>
          <label className="inline-flex items-center gap-2 rounded-xl border border-line bg-white px-3 py-2">
            <Languages aria-hidden="true" className="size-4 text-brand-800" />
            <span className="sr-only">{t("language")}</span>
            <select
              value={locale}
              onChange={(event) => setLocale(event.target.value as typeof locale)}
              className="min-h-8 bg-transparent text-sm font-semibold focus:outline-none"
              aria-label={t("language")}
            >
              <option value="en">English</option>
              <option value="hi">हिन्दी</option>
              <option value="bn">বাংলা</option>
              <option value="te">తెలుగు</option>
            </select>
          </label>
        </div>

        <div className="grid gap-6 lg:grid-cols-[1.05fr_1fr] lg:items-start">
          <section>
            <p className="mb-2 inline-flex items-center gap-2 rounded-full border border-brand-200 bg-brand-50 px-3 py-1 text-xs font-bold uppercase tracking-wide text-brand-900">
              <ShieldCheck aria-hidden="true" className="size-4" />
              {t("signIn.heroEyebrow")}
            </p>
            <h1 className="text-3xl leading-tight sm:text-4xl">{t("signIn.heroTitle")}</h1>
            <p className="mt-3 max-w-2xl text-[15px] leading-relaxed text-muted">{t("signIn.heroLead")}</p>

            <div className="mt-6 grid gap-3 sm:grid-cols-2">
              <Card className="p-4">
                <div className="flex items-center gap-2 text-brand-900">
                  <UsersRound aria-hidden="true" className="size-5" />
                  <p className="text-sm font-bold">{t("signIn.membersCard")}</p>
                </div>
                <p className="mt-1 text-xs leading-relaxed text-muted">{t("signIn.membersCardBody")}</p>
              </Card>
              <Card className="p-4">
                <div className="flex items-center gap-2 text-brand-900">
                  <Globe2 aria-hidden="true" className="size-5" />
                  <p className="text-sm font-bold">{t("signIn.migrationCard")}</p>
                </div>
                <p className="mt-1 text-xs leading-relaxed text-muted">{t("signIn.migrationCardBody")}</p>
              </Card>
            </div>

            <Notice tone="warning" className="mt-6" title={t("signIn.notDoTitle")}>
              <p>{t("signIn.notDoBody1")}</p>
              <p>{t("signIn.notDoBody2")}</p>
            </Notice>

            <div className="mt-6 flex flex-wrap gap-4 text-sm">
              <Link to="/public" className="link">
                {t("signIn.publicStatsLink")}
              </Link>
              <Link to="/signin#accessibility" className="link">
                {t("signIn.a11yLink")}
              </Link>
            </div>

            <section id="accessibility" className="mt-6 rounded-xl border border-line bg-white p-4">
              <h2 className="text-sm font-bold">{t("signIn.sharedDesignTitle")}</h2>
              <p className="mt-1 text-xs leading-relaxed text-muted">{t("signIn.sharedDesignBody")}</p>
            </section>
          </section>

          <Card>
            <div className="flex items-start justify-between gap-3">
              <div>
                <h2 className="text-xl">{t("signIn")}</h2>
                <p className="mt-1 text-sm text-muted">{t("signIn.choosePrompt")}</p>
              </div>
              <span className="chip border-amber-300 bg-warningBg text-amber-950">DEMO</span>
            </div>

            {loading ? <div className="mt-4"><LoadingState /></div> : null}
            {error ? <div className="mt-4"><ErrorState message={error} onRetry={load} /></div> : null}

            {!loading && !error ? (
              <>
                <div className="mt-4">
                  <p className="label">{t("signIn.householdList")}</p>
                  <div className="grid gap-2">
                    {households.map((item) => (
                      <button
                        key={item.id}
                        type="button"
                        onClick={() => setSelected(item.id)}
                        aria-pressed={selected === item.id}
                        className={cn(
                          "flex min-h-14 w-full items-center gap-3 rounded-xl border p-3 text-left transition-colors",
                          selected === item.id
                            ? "border-brand-700 bg-brand-50"
                            : "border-line bg-white hover:bg-canvas",
                        )}
                      >
                        <Building2 aria-hidden="true" className="size-5 shrink-0 text-brand-800" />
                        <span className="min-w-0">
                          <span className="block truncate text-sm font-semibold">{item.label}</span>
                          <span className="block truncate text-xs text-muted">
                            {item.reference} · {item.home_state} → {item.destination_state}
                          </span>
                        </span>
                      </button>
                    ))}
                  </div>
                </div>

                {household ? (
                  <div className="mt-5">
                    <p className="label">{t("signIn.memberProfiles")}</p>
                    <ul className="space-y-2">
                      {household.members.map((member) => (
                        <li key={member.id}>
                          <div className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-line p-3">
                            <div className="min-w-0">
                              <p className="truncate text-sm font-semibold">
                                {member.alias}
                                {member.is_head ? ` — ${t("signIn.head")}` : ""}
                                {member.is_absent ? ` (${t("signIn.absent")})` : ""}
                              </p>
                              <p className="text-xs text-muted">
                                {member.relationship ?? "Member"} · {member.age_band}
                              </p>
                            </div>
                            <Button
                              variant="secondary"
                              className="min-h-9 px-3 py-1.5 text-xs"
                              onClick={() => startMember(member.id)}
                              disabled={busy}
                              aria-label={t("signIn.continueAs", { name: member.alias })}
                            >
                              {t("signIn.continue")}
                              <ArrowRight aria-hidden="true" className="size-4" />
                            </Button>
                          </div>
                        </li>
                      ))}
                    </ul>

                    <div className="mt-4 rounded-xl border border-dashed border-line p-3">
                      <p className="text-sm font-semibold">{t("signIn.facilitatorTitle")}</p>
                      <p className="mt-1 text-xs leading-relaxed text-muted">{t("signIn.facilitatorBody")}</p>
                      <Button className="mt-3" variant="secondary" onClick={startFacilitator} disabled={busy}>
                        <LogIn aria-hidden="true" className="size-4" />
                        {t("signIn.facilitatorStart")}
                      </Button>
                    </div>
                  </div>
                ) : null}
              </>
            ) : null}
          </Card>
        </div>
      </div>
    </div>
  );
}
