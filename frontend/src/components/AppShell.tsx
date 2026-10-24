import {
  ArrowLeftRight,
  ClipboardList,
  FileSearch,
  Gauge,
  Globe2,
  HelpCircle,
  Home,
  Languages,
  LogOut,
  Scale,
  Settings,
  ShieldCheck,
  TestTube2,
  UserRound,
  UsersRound,
  X
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { api, ApiError } from "../lib/api";
import { useI18n } from "../lib/i18n";
import type { DemoHousehold } from "../lib/types";
import { useSession } from "../app/session";
import { DemoBanner } from "./DemoBanner";
import { Button, Modal, Notice, cn } from "./ui";

const NAV = [
  { to: "/", key: "nav.overview", icon: Home, end: true },
  { to: "/member", key: "nav.record", icon: UserRound },
  { to: "/migration", key: "nav.migration", icon: Globe2 },
  { to: "/corrections", key: "nav.corrections", icon: ArrowLeftRight, fallback: "Corrections" },
  { to: "/drafts", key: "nav.drafts", icon: ClipboardList },
  { to: "/grievances", key: "nav.grievances", icon: Scale },
  { to: "/public", key: "nav.public", icon: FileSearch },
  { to: "/settings", key: "nav.settings", icon: Settings },
  { to: "/demo", key: "nav.demo", icon: TestTube2 }
] as const;

const MOBILE_NAV = NAV.filter((item) =>
  ["/", "/migration", "/corrections", "/drafts", "/grievances"].includes(item.to),
);

function BrandMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 48 48" className={cn("size-9", className)} role="img" aria-label="RationSaathi logo">
      <rect width="48" height="48" rx="12" fill="#14532d" />
      <path d="M13 29c0-7 5-12 11-12s11 5 11 12" stroke="#dcefdf" strokeWidth="3" strokeLinecap="round" fill="none" />
      <path d="M24 17v15M17 32h14" stroke="#8cc99a" strokeWidth="3" strokeLinecap="round" />
      <circle cx="24" cy="13" r="2.6" fill="#fef3c7" />
    </svg>
  );
}

function countdownLabel(iso: string): string {
  const ms = new Date(iso).getTime() - Date.now();
  if (ms <= 0) return "expired";
  const minutes = Math.floor(ms / 60000);
  if (minutes < 1) return "under a minute";
  return `${minutes} min`;
}

export function AppShell() {
  const { session, epoch, endSession, switchProfile } = useSession();
  const { t, locale, setLocale, languageLabel, isTranslated } = useI18n();
  const navigate = useNavigate();
  const location = useLocation();
  const [switcherOpen, setSwitcherOpen] = useState(false);
  const [endOpen, setEndOpen] = useState(false);
  const [helpOpen, setHelpOpen] = useState(false);
  const [profiles, setProfiles] = useState<DemoHousehold[]>([]);
  const [profilesError, setProfilesError] = useState("");
  const [busy, setBusy] = useState(false);
  const [cleanupMessage, setCleanupMessage] = useState("");
  const [expiresIn, setExpiresIn] = useState(() => (session ? countdownLabel(session.expires_at) : ""));

  useEffect(() => {
    if (!session) return;
    setExpiresIn(countdownLabel(session.expires_at));
    const interval = window.setInterval(() => setExpiresIn(countdownLabel(session.expires_at)), 30_000);
    return () => window.clearInterval(interval);
  }, [session]);

  useEffect(() => {
    if (new URLSearchParams(location.search).has("member")) {
      // Defensive: never let sensitive identifiers live in a URL.
      navigate(location.pathname, { replace: true });
    }
  }, [location, navigate]);

  const loadProfiles = useCallback(async () => {
    setProfilesError("");
    try {
      const payload = await api.demoProfiles();
      setProfiles(payload.households);
    } catch (error) {
      setProfilesError(error instanceof ApiError ? error.message : "Could not load demo profiles.");
    }
  }, []);

  const openSwitcher = () => {
    setSwitcherOpen(true);
    void loadProfiles();
  };

  const handleSwitch = async (memberId: string) => {
    setBusy(true);
    setProfilesError("");
    try {
      const notice = await switchProfile(memberId);
      setSwitcherOpen(false);
      setCleanupMessage(`${t("sessionPrivacy")} ${notice}`);
      navigate("/", { replace: true });
    } catch (error) {
      setProfilesError(error instanceof ApiError ? error.message : "Could not switch profile.");
    } finally {
      setBusy(false);
    }
  };

  const handleEnd = async () => {
    setBusy(true);
    await endSession("USER_LOGOUT");
    setBusy(false);
    setEndOpen(false);
    navigate("/exit", { replace: true });
  };

  const currentMember = session?.member;
  const isFacilitator = session?.role === "FACILITATOR";
  const nav = useMemo(() => NAV, []);

  if (!session) return null;

  return (
    <div className="min-h-screen bg-canvas">
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>
      <DemoBanner />
      <div className="mx-auto flex max-w-[1400px]">
        <aside className="sticky top-0 hidden h-screen w-72 shrink-0 flex-col border-r border-line bg-[#f7f3e9] px-4 py-6 lg:flex">
          <NavLink to="/" className="mb-6 flex items-center gap-3 rounded-xl p-1">
            <BrandMark />
            <span>
              <span className="block text-lg font-bold leading-tight text-brand-900">{t("appName")}</span>
              <span className="block text-[11px] leading-tight text-muted">{t("tagline")}</span>
            </span>
          </NavLink>

          <div className="mb-4 rounded-xl border border-line bg-white p-3">
            <p className="text-[11px] font-bold uppercase tracking-wide text-muted">Household</p>
            <p className="mt-0.5 text-sm font-semibold">{session.household.reference}</p>
            <p className="text-xs text-muted">
              {session.household.home_state} → {session.household.destination_state}
            </p>
            <p className="mt-2 inline-flex items-center gap-1 rounded-full bg-brand-50 px-2 py-0.5 text-[11px] font-semibold text-brand-900">
              <ShieldCheck aria-hidden="true" className="size-3" />
              {isFacilitator ? "Assisted session" : t("profile")}: {currentMember?.alias ?? "not selected"}
            </p>
          </div>

          <nav aria-label="Main navigation" className="flex-1">
            <ul className="space-y-1">
              {nav.map((item) => {
                const Icon = item.icon;
                const label = "fallback" in item ? item.fallback : t(item.key as Parameters<typeof t>[0]);
                return (
                  <li key={item.to}>
                    <NavLink
                      to={item.to}
                      end={"end" in item && item.end}
                      className={({ isActive }) =>
                        cn(
                          "flex min-h-11 items-center gap-3 rounded-xl px-3 py-2 text-sm font-semibold transition-colors",
                          isActive
                            ? "bg-brand-800 text-white"
                            : "text-ink hover:bg-brand-50 hover:text-brand-900",
                        )
                      }
                    >
                      <Icon aria-hidden="true" className="size-5" />
                      {label}
                    </NavLink>
                  </li>
                );
              })}
            </ul>
          </nav>

          <div className="mt-4 space-y-2">
            <Button variant="secondary" className="w-full justify-start" onClick={() => setHelpOpen(true)}>
              <HelpCircle aria-hidden="true" className="size-4" />
              {t("help")}
            </Button>
            <Button variant="danger" className="w-full justify-start" onClick={() => setEndOpen(true)}>
              <LogOut aria-hidden="true" className="size-4" />
              {t("endSession")}
            </Button>
            <p className="px-1 text-[11px] leading-relaxed text-muted">
              {t("privacy.handover")}
            </p>
          </div>
        </aside>

        <div className="min-w-0 flex-1">
          <header className="sticky top-0 z-30 border-b border-line bg-canvas/95 backdrop-blur">
            <div className="flex flex-wrap items-center gap-2 px-4 py-3 sm:px-6">
              <NavLink to="/" className="flex items-center gap-2 lg:hidden">
                <BrandMark className="size-8" />
                <span className="text-base font-bold text-brand-900">{t("appName")}</span>
              </NavLink>

              <div className="ml-auto flex flex-wrap items-center gap-2">
                <div className="hidden items-center gap-1.5 rounded-full border border-line bg-white px-3 py-1.5 text-xs font-medium text-muted sm:flex">
                  <span className="inline-flex size-2 rounded-full bg-brand-600" aria-hidden="true" />
                  {t("sessionActive")} · {expiresIn}
                </div>

                <label className="relative inline-flex items-center gap-1.5 rounded-xl border border-line bg-white px-2 py-1.5">
                  <Languages aria-hidden="true" className="size-4 text-brand-800" />
                  <span className="sr-only">{t("language")}</span>
                  <select
                    value={locale}
                    onChange={(event) => setLocale(event.target.value as typeof locale)}
                    className="min-h-8 cursor-pointer appearance-none bg-transparent pr-1 text-sm font-semibold text-ink focus:outline-none"
                    aria-label={`${t("language")} — ${languageLabel}`}
                  >
                    <option value="en">English</option>
                    <option value="hi">हिन्दी</option>
                    <option value="bn">বাংলা</option>
                    <option value="te">తెలుగు</option>
                  </select>
                </label>

                <Button variant="secondary" className="min-h-9 px-3 py-1.5 text-xs" onClick={openSwitcher}>
                  <UsersRound aria-hidden="true" className="size-4" />
                  <span className="hidden sm:inline">{t("switchProfile")}</span>
                  <span className="sm:hidden">{currentMember?.alias ?? "Profile"}</span>
                </Button>

                <Button
                  variant="danger"
                  className="min-h-9 px-3 py-1.5 text-xs lg:hidden"
                  onClick={() => setEndOpen(true)}
                  aria-label={t("endSession")}
                >
                  <LogOut aria-hidden="true" className="size-4" />
                </Button>
              </div>
            </div>

            <div className="flex items-center gap-2 px-4 pb-2 text-xs text-muted sm:px-6">
              <span className="inline-flex items-center gap-1 rounded-full bg-white px-2 py-1 font-semibold text-brand-900 ring-1 ring-line">
                <UserRound aria-hidden="true" className="size-3.5" />
                {isFacilitator ? "Facilitator" : currentMember?.alias ?? "No profile"}
              </span>
              <span aria-hidden="true">·</span>
              <span>{t("sessionPrivacy")}</span>
              {locale !== "en" ? (
                <>
                  <span aria-hidden="true">·</span>
                  <span>{t("common.englishFallback")}</span>
                </>
              ) : null}
            </div>
          </header>

          {cleanupMessage ? (
            <div className="px-4 pt-4 sm:px-6">
              <Notice tone="success" ariaLive="polite" title="Profile switched">
                {cleanupMessage}
              </Notice>
            </div>
          ) : null}

          <main id="main-content" className="mx-auto w-full max-w-6xl px-4 pb-28 pt-5 sm:px-6 sm:pt-7 lg:pb-10">
            <Outlet key={`${session.role}-${session.member?.id ?? "none"}-${epoch}`} />
          </main>
        </div>
      </div>

      <nav
        aria-label="Quick navigation"
        className="fixed inset-x-0 bottom-0 z-30 border-t border-line bg-white/98 pb-[env(safe-area-inset-bottom)] lg:hidden"
      >
        <ul className="grid grid-cols-5">
          {MOBILE_NAV.map((item) => {
            const Icon = item.icon;
            const label = "fallback" in item ? item.fallback : t(item.key as Parameters<typeof t>[0]);
            return (
              <li key={item.to}>
                <NavLink
                  to={item.to}
                  end={"end" in item && item.end}
                  className={({ isActive }) =>
                    cn(
                      "flex min-h-14 flex-col items-center justify-center gap-0.5 px-1 py-2 text-[10px] font-semibold",
                      isActive ? "text-brand-900" : "text-muted",
                    )
                  }
                >
                  <Icon aria-hidden="true" className="size-5" />
                  <span className="truncate">{label}</span>
                </NavLink>
              </li>
            );
          })}
        </ul>
      </nav>

      <Modal
        open={switcherOpen}
        onClose={() => setSwitcherOpen(false)}
        title={t("switchProfile")}
        description="This is the synthetic demo sign-in directory. The current session token is revoked and in-memory private data is cleared before the new profile renders."
      >
        <Notice tone="warning" title="Shared device">
          Only switch profiles if you are the person entitled to use the next profile, or if you are a facilitator with
          recorded consent. Profile switching does not prove identity.
        </Notice>
        <div className="mt-4 space-y-4">
          {profilesError ? <Notice tone="danger">{profilesError}</Notice> : null}
          {profiles.map((household) => (
            <div key={household.id}>
              <p className="text-sm font-bold text-ink">{household.label}</p>
              <p className="text-xs text-muted">
                {household.reference} · {household.home_state} → {household.destination_state}
              </p>
              <ul className="mt-2 space-y-2">
                {household.members.map((member) => (
                  <li key={member.id}>
                    <div className="flex items-center justify-between gap-3 rounded-xl border border-line bg-white p-3">
                      <div>
                        <p className="text-sm font-semibold">
                          {member.alias}
                          {member.is_head ? " (head)" : ""}
                          {member.is_absent ? " — absent" : ""}
                        </p>
                        <p className="text-xs text-muted">
                          {member.relationship ?? "member"} · {member.age_band} · {member.verification_state}
                        </p>
                      </div>
                      <Button
                        variant="secondary"
                        disabled={busy || member.id === currentMember?.id}
                        onClick={() => handleSwitch(member.id)}
                        aria-label={`Switch to ${member.alias}`}
                      >
                        {member.id === currentMember?.id ? "Current" : "Open"}
                      </Button>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          ))}
          {profiles.length === 0 && !profilesError ? <p className="text-sm text-muted">Loading profiles…</p> : null}
          {isFacilitator ? (
            <Notice tone="warning">
              A facilitator must end this assisted session and start a new one with fresh consent to change households.
            </Notice>
          ) : null}
        </div>
      </Modal>

      <Modal
        open={endOpen}
        onClose={() => setEndOpen(false)}
        title={t("endSession")}
        description="The server session is revoked. Private React state, drafts held in memory and any object URLs are discarded. Browser/OS artifacts outside the app may persist."
        footer={
          <>
            <Button variant="secondary" onClick={() => setEndOpen(false)}>
              {t("common.cancel")}
            </Button>
            <Button variant="danger" onClick={handleEnd} disabled={busy}>
              {busy ? "Ending…" : t("endSession")}
            </Button>
          </>
        }
      >
        <Notice tone="warning" title="Before you hand over the device">
          <p>Ending the session does not remove screenshots, OS backups or external copies of information.</p>
          <p>It does revoke the token, clear this tab's private state and require a fresh session for any profile.</p>
        </Notice>
      </Modal>

      <Modal
        open={helpOpen}
        onClose={() => setHelpOpen(false)}
        title="How to use this demo"
        description="RationSaathi shows what is verified, what is uncertain and who to contact. It never changes an official record."
      >
        <ul className="space-y-2 text-sm leading-relaxed text-ink">
          <li>• Start at Overview to see today's safe next steps and the 21-day-old grievance.</li>
          <li>• My record shows this member's entitlements and provenance. Other members stay hidden.</li>
          <li>• Migration explains portability and stock uncertainty without promising availability.</li>
          <li>• Corrections simulates a mismatch fix and blocks entitlement-removing changes.</li>
          <li>• Drafts keeps "not submitted" separate from a verified official submission.</li>
          <li>• Grievances tracks the case and generates an editable escalation draft.</li>
          <li>• Public data contains suppressed aggregates only.</li>
        </ul>
        <Notice tone="info" className="mt-4">
          No government integration is connected. Every submission uses the labelled demo adapter.
        </Notice>
      </Modal>
    </div>
  );
}
