import { Accessibility, Globe2, Languages, LogOut, ShieldOff, Volume2 } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useSession } from "../../app/session";
import { PictogramLegend } from "../../components/Pictogram";
import { ReadAloud } from "../../components/ReadAloud";
import { Button, Card, DataRow, Notice, PageHeader, cn } from "../../components/ui";
import { LANGUAGES, useI18n, type LocaleCode } from "../../lib/i18n";

const PREFS_KEY = "rationsaathi.a11y";

interface Prefs {
  largeText: boolean;
  reduceMotion: boolean;
  speechRate: number;
}

function loadPrefs(): Prefs {
  try {
    const raw = localStorage.getItem(PREFS_KEY);
    if (raw) {
      const parsed = JSON.parse(raw) as Partial<Prefs>;
      return {
        largeText: Boolean(parsed.largeText),
        reduceMotion: Boolean(parsed.reduceMotion),
        speechRate: typeof parsed.speechRate === "number" ? parsed.speechRate : 0.95,
      };
    }
  } catch {
    // Preferences are non-sensitive; fall back to defaults.
  }
  return { largeText: false, reduceMotion: false, speechRate: 0.95 };
}

export function SettingsPage() {
  const { session, endSession } = useSession();
  const { t, locale, setLocale } = useI18n();
  const navigate = useNavigate();
  const [prefs, setPrefs] = useState<Prefs>(loadPrefs);

  useEffect(() => {
    document.documentElement.classList.toggle("large-text", prefs.largeText);
    document.documentElement.classList.toggle("reduce-motion", prefs.reduceMotion);
    try {
      localStorage.setItem(PREFS_KEY, JSON.stringify(prefs));
    } catch {
      // Ignore storage failures.
    }
  }, [prefs]);

  const handleEnd = async () => {
    await endSession("USER_LOGOUT");
    navigate("/exit", { replace: true });
  };

  if (!session) return null;

  return (
    <div>
      <PageHeader
        eyebrow="Settings"
        title={t("a11y.title")}
        description="Language and accessibility preferences are non-sensitive and stored only on this device. Private profile data is never stored there."
        icon={<Accessibility aria-hidden="true" className="size-5" />}
      />

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <h2 className="section-title flex items-center gap-2">
            <Languages aria-hidden="true" className="size-5 text-brand-800" />
            {t("language")}
          </h2>
          <p className="mt-1 text-sm text-muted">
            Critical safety messages are translated. Some secondary content may remain in English and is labelled.
          </p>
          <div className="mt-3 grid gap-2 sm:grid-cols-2" role="group" aria-label="Choose language">
            {LANGUAGES.map((language) => (
              <button
                key={language.code}
                type="button"
                aria-pressed={locale === language.code}
                onClick={() => setLocale(language.code as LocaleCode)}
                className={cn(
                  "min-h-12 rounded-xl border px-3 text-left text-sm font-semibold",
                  locale === language.code
                    ? "border-brand-800 bg-brand-50 text-brand-950"
                    : "border-line bg-white hover:bg-canvas",
                )}
              >
                <span className="block">{language.native}</span>
                <span className="block text-xs font-normal text-muted">{language.label}</span>
              </button>
            ))}
          </div>
          <p className="mt-2 text-xs text-muted">
            Translations are project-authored for this prototype and should be reviewed by native speakers before use in
            safety-critical deployment.
          </p>
        </Card>

        <Card>
          <h2 className="section-title flex items-center gap-2">
            <Volume2 aria-hidden="true" className="size-5 text-brand-800" />
            Accessibility controls
          </h2>
          <div className="mt-3 space-y-3">
            <label className="flex min-h-11 items-center justify-between gap-3 rounded-xl border border-line p-3 text-sm">
              <span>{t("a11y.largeText")}</span>
              <input
                type="checkbox"
                className="size-5 accent-brand-800"
                checked={prefs.largeText}
                onChange={(event) => setPrefs({ ...prefs, largeText: event.target.checked })}
              />
            </label>
            <label className="flex min-h-11 items-center justify-between gap-3 rounded-xl border border-line p-3 text-sm">
              <span>{t("a11y.reduceMotion")}</span>
              <input
                type="checkbox"
                className="size-5 accent-brand-800"
                checked={prefs.reduceMotion}
                onChange={(event) => setPrefs({ ...prefs, reduceMotion: event.target.checked })}
              />
            </label>
            <label className="block rounded-xl border border-line p-3 text-sm">
              <span className="mb-1 block font-semibold">{t("a11y.speechRate")}</span>
              <input
                type="range"
                min={0.6}
                max={1.3}
                step={0.05}
                value={prefs.speechRate}
                onChange={(event) => setPrefs({ ...prefs, speechRate: Number(event.target.value) })}
                className="w-full accent-brand-800"
                aria-valuemin={0.6}
                aria-valuemax={1.3}
                aria-valuenow={prefs.speechRate}
              />
              <span className="text-xs text-muted">{prefs.speechRate.toFixed(2)}× — browser speech availability varies.</span>
            </label>
          </div>
          <ReadAloud
            text={`Accessibility settings. ${t("a11y.voiceUnavailable")} ${t("a11y.largeText")}. ${t("a11y.reduceMotion")}.`}
            label="Test the spoken feedback"
            rate={prefs.speechRate}
          />
        </Card>
      </div>

      <Card className="mt-4">
        <h2 className="section-title">Session and privacy</h2>
        <dl className="mt-2">
          <DataRow label="Household">{session.household.reference}</DataRow>
          <DataRow label="Role">{session.role}</DataRow>
          <DataRow label="Member">{session.member?.alias ?? "No member scope"}</DataRow>
          <DataRow label="Expires">{new Date(session.expires_at).toLocaleString()}</DataRow>
          <DataRow label="Consent grants">
            {session.consent_member_ids.length ? `${session.consent_member_ids.length} member(s)` : "None"}
          </DataRow>
        </dl>
        <Notice tone="warning" className="mt-3" title="Shared-device limitations">
          <p>This app holds the session token in memory only and clears state on logout, profile switch and expiry.</p>
          <p>
            It cannot guarantee deletion of operating-system backups, screenshots, or copies made outside the app. Minimise
            what is displayed and end the session before handover.
          </p>
        </Notice>
        <div className="mt-3 flex flex-wrap gap-2">
          <Button variant="danger" onClick={handleEnd}>
            <LogOut aria-hidden="true" className="size-4" />
            {t("endSession")}
          </Button>
          <span className="inline-flex items-center gap-1 text-xs text-muted">
            <ShieldOff aria-hidden="true" className="size-4" />
            Refreshing the page also ends access in this tab because no token is persisted.
          </span>
        </div>
      </Card>

      <Card className="mt-4">
        <h2 className="section-title flex items-center gap-2">
          <Globe2 aria-hidden="true" className="size-5 text-brand-800" />
          {t("a11y.pictograms")}
        </h2>
        <p className="mt-1 text-sm text-muted">Every status has a label and icon; colour is never the only signal.</p>
        <div className="mt-3">
          <PictogramLegend />
        </div>
      </Card>
    </div>
  );
}
