import { CheckCircle2, HandHeart, ShieldCheck, UsersRound } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useSession } from "../../app/session";
import { ReadAloud } from "../../components/ReadAloud";
import { Button, Card, ErrorState, LoadingState, Notice, PageHeader } from "../../components/ui";
import { api, ApiError } from "../../lib/api";
import { useI18n } from "../../lib/i18n";
import type { DemoHousehold } from "../../lib/types";

export function FacilitatorConsentPage() {
  const { session, recordConsent } = useSession();
  const { t } = useI18n();
  const navigate = useNavigate();
  const [household, setHousehold] = useState<DemoHousehold | null>(null);
  const [selected, setSelected] = useState<string>("");
  const [explained, setExplained] = useState(false);
  const [given, setGiven] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!session) return;
    api
      .demoProfiles()
      .then((payload) => {
        const match = payload.households.find((item) => item.id === session.household.id) ?? null;
        setHousehold(match);
        setSelected(match?.members[0]?.id ?? "");
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load household profiles."))
      .finally(() => setLoading(false));
  }, [session]);

  if (!session) return null;
  if (session.role !== "FACILITATOR") {
    return (
      <Notice tone="info">
        This screen is only used for assisted-service sessions.{" "}
        <button type="button" className="link" onClick={() => navigate("/")}>
          Return to your profile
        </button>
      </Notice>
    );
  }

  const consent = async () => {
    if (!selected) return;
    setBusy(true);
    setError("");
    try {
      await recordConsent(selected, explained, given);
      navigate("/", { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not record consent.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div>
      <PageHeader
        eyebrow="Assisted service"
        title="Consent before any profile opens"
        description="Explain what will be shown, why it is needed and who can see it. Record consent for one member only; this session cannot open a second member without a fresh session."
        icon={<HandHeart aria-hidden="true" className="size-5" />}
      />

      {loading ? <LoadingState /> : null}
      {error && !household ? <ErrorState message={error} onRetry={() => window.location.reload()} /> : null}

      {household ? (
        <div className="grid gap-4 lg:grid-cols-2">
          <Card>
            <h2 className="section-title flex items-center gap-2">
              <UsersRound aria-hidden="true" className="size-5" />
              Household {household.reference}
            </h2>
            <p className="mt-1 text-sm text-muted">
              Only aliases are shown for consent selection. Sensitive entitlement values stay closed until consent and a
              member scope are recorded.
            </p>
            <ul className="mt-3 space-y-2">
              {household.members.map((member) => (
                <li key={member.id}>
                  <button
                    type="button"
                    aria-pressed={selected === member.id}
                    onClick={() => setSelected(member.id)}
                    className={`min-h-12 w-full rounded-xl border p-3 text-left ${
                      selected === member.id ? "border-brand-800 bg-brand-50" : "border-line bg-white"
                    }`}
                  >
                    <span className="block text-sm font-semibold">
                      {member.alias}
                      {member.is_dependent ? " — dependent" : ""}
                    </span>
                    <span className="block text-xs text-muted">{member.relationship ?? "member"}</span>
                  </button>
                </li>
              ))}
            </ul>
          </Card>

          <Card>
            <h2 className="section-title">Consent conversation</h2>
            <ol className="mt-2 space-y-2 text-sm text-muted">
              <li>1. Say what information will be viewed or entered.</li>
              <li>2. Explain why it is needed for the requested service.</li>
              <li>3. Explain that a draft is not an official submission.</li>
              <li>4. Explain that the session will be ended and cleared afterwards.</li>
            </ol>
            <div className="mt-4 space-y-3">
              <label className="flex min-h-11 items-start gap-3 rounded-xl border border-line p-3 text-sm">
                <input
                  type="checkbox"
                  className="mt-1 size-5 accent-brand-800"
                  checked={explained}
                  onChange={(event) => setExplained(event.target.checked)}
                />
                <span>I explained what is collected, why, who can see it, and how to end the session.</span>
              </label>
              <label className="flex min-h-11 items-start gap-3 rounded-xl border border-line p-3 text-sm">
                <input
                  type="checkbox"
                  className="mt-1 size-5 accent-brand-800"
                  checked={given}
                  onChange={(event) => setGiven(event.target.checked)}
                />
                <span>The member gave consent for this assisted session. I did not assume consent for another adult.</span>
              </label>
            </div>
            <Button className="mt-4" onClick={consent} disabled={busy || !explained || !given || !selected}>
              <CheckCircle2 aria-hidden="true" className="size-4" />
              Record consent and open profile
            </Button>
            {error ? <Notice tone="danger" className="mt-3">{error}</Notice> : null}
            <ReadAloud
              text="A facilitator session records consent for one member only. A local draft is not an official submission. End the session before handing over the device."
              label="Read the consent explanation"
            />
          </Card>

          <Card className="lg:col-span-2">
            <h2 className="section-title flex items-center gap-2">
              <ShieldCheck aria-hidden="true" className="size-5 text-brand-800" />
              {t("privacy.title")}
            </h2>
            <p className="mt-1 text-sm text-muted">
              Ending the assisted session revokes the token and invalidates consent. The next household cannot use the back
              button to recover this profile because no token or private state survives. Screenshots and OS-level copies are
              outside the application's control.
            </p>
          </Card>
        </div>
      ) : null}
    </div>
  );
}
