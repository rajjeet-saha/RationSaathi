import { CheckCircle2, LogIn, ShieldCheck, XCircle } from "lucide-react";
import { Link } from "react-router-dom";
import { useSession } from "../../app/session";
import { Card, Notice, PageHeader } from "../../components/ui";

export function ExitPage() {
  const { lastCleanup } = useSession();

  return (
    <div className="mx-auto max-w-3xl px-4 py-10 sm:px-6">
      <PageHeader
        eyebrow="Session terminated"
        title="Cleanup verification"
        description="The server session is revoked and this tab's private state has been discarded. Some device-level artifacts cannot be deleted by a web application."
        icon={<ShieldCheck aria-hidden="true" className="size-5" />}
      />

      {lastCleanup ? (
        <Card>
          <div className="flex items-center gap-2">
            {lastCleanup.ended ? (
              <CheckCircle2 aria-hidden="true" className="size-6 text-brand-700" />
            ) : (
              <XCircle aria-hidden="true" className="size-6 text-danger" />
            )}
            <div>
              <h2 className="section-title">{lastCleanup.ended ? "Session ended" : "Session state uncertain"}</h2>
              <p className="text-xs text-muted">
                Reason: {lastCleanup.ended_reason.replaceAll("_", " ").toLowerCase()} · server cleanup verified:{" "}
                {lastCleanup.server_cleanup_verified ? "yes" : "not confirmed"}
              </p>
            </div>
          </div>

          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <div>
              <h3 className="text-sm font-bold uppercase tracking-wide text-muted">Server actions</h3>
              <ul className="mt-1 space-y-1 text-sm">
                {lastCleanup.server_actions.map((action) => (
                  <li key={action}>• {action}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="text-sm font-bold uppercase tracking-wide text-muted">Client actions required</h3>
              <ul className="mt-1 space-y-1 text-sm">
                {lastCleanup.client_actions_required.map((action) => (
                  <li key={action}>• {action}</li>
                ))}
              </ul>
            </div>
          </div>

          <Notice tone="warning" className="mt-4" title="Honest limitations">
            <ul className="space-y-1">
              {lastCleanup.limitations.map((item) => (
                <li key={item}>• {item}</li>
              ))}
            </ul>
          </Notice>

          {lastCleanup.household_reference ? (
            <p className="mt-3 text-xs text-muted">
              Household scope closed: {lastCleanup.household_reference}. No further data can be loaded with the old token.
            </p>
          ) : null}
        </Card>
      ) : (
        <Notice tone="info" title="No cleanup record in memory">
          <p>
            No session is active in this tab. Cleanup details are held only in memory after an explicit session end; a
            refresh clears them too. Start a new session to continue.
          </p>
        </Notice>
      )}

      <div className="mt-4 flex flex-wrap gap-2">
        <Link to="/signin" className="btn-primary">
          <LogIn aria-hidden="true" className="size-4" />
          Start a new session
        </Link>
        <Link to="/public" className="btn-secondary">
          View public statistics
        </Link>
      </div>

      <p className="mt-6 text-xs text-muted">
        If this is a shared device, close the tab and ask the facilitator to verify the screen with you. A web app cannot
        guarantee deletion of screenshots or operating-system backups.
      </p>
    </div>
  );
}
