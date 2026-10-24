import { useEffect } from "react";
import { BrowserRouter, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { AppShell } from "../components/AppShell";
import { PublicPage } from "../features/analytics/PublicPage";
import { SettingsPage } from "../features/accessibility/SettingsPage";
import { CorrectionsPage } from "../features/corrections/CorrectionsPage";
import { DraftsPage } from "../features/drafts/DraftsPage";
import { GrievanceDetailPage } from "../features/grievances/GrievanceDetailPage";
import { GrievancesPage } from "../features/grievances/GrievancesPage";
import { MemberPage } from "../features/household/MemberPage";
import { OverviewPage } from "../features/household/OverviewPage";
import { MigrationPage } from "../features/portability/MigrationPage";
import { DemoPage } from "../features/session/DemoPage";
import { ExitPage } from "../features/session/ExitPage";
import { FacilitatorConsentPage } from "../features/session/FacilitatorConsentPage";
import { SignInPage } from "../features/session/SignInPage";
import { useSession } from "./session";
import { Button } from "../components/ui";

function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "auto" });
  }, [pathname]);
  return null;
}

function ShellGate() {
  const { session } = useSession();
  const location = useLocation();
  if (!session) return <Navigate to="/signin" replace />;
  if (
    session.role === "FACILITATOR" &&
    !session.member &&
    location.pathname !== "/facilitator" &&
    location.pathname !== "/settings"
  ) {
    return <Navigate to="/facilitator" replace />;
  }
  return <AppShell />;
}

function PublicRoute() {
  const { session } = useSession();
  return <PublicPage standalone={!session} />;
}

function SignInRoute() {
  const { session } = useSession();
  if (session) return <Navigate to="/" replace />;
  return <SignInPage />;
}

function NotFound() {
  return (
    <div className="mx-auto max-w-xl px-4 py-16 text-center">
      <h1 className="text-2xl">Page not found</h1>
      <p className="mt-2 text-sm text-muted">This route does not exist in the RationSaathi demo.</p>
      <Button className="mt-4" onClick={() => window.location.assign("/")}>
        Back to overview
      </Button>
    </div>
  );
}

export function App() {
  return (
    <BrowserRouter>
      <ScrollToTop />
      <Routes>
        <Route path="/signin" element={<SignInRoute />} />
        <Route path="/public" element={<PublicRoute />} />
        <Route path="/exit" element={<ExitPage />} />
        <Route element={<ShellGate />}>
          <Route path="/" element={<OverviewPage />} />
          <Route path="/member" element={<MemberPage />} />
          <Route path="/migration" element={<MigrationPage />} />
          <Route path="/corrections" element={<CorrectionsPage />} />
          <Route path="/drafts" element={<DraftsPage />} />
          <Route path="/grievances" element={<GrievancesPage />} />
          <Route path="/grievances/:id" element={<GrievanceDetailPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/demo" element={<DemoPage />} />
          <Route path="/facilitator" element={<FacilitatorConsentPage />} />
        </Route>
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}
