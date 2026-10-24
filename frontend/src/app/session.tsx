import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { api, onUnauthorized, setSessionToken } from "../lib/api";
import type { CleanupResult, SessionPayload } from "../lib/types";

interface SessionValue {
  session: SessionPayload | null;
  ready: boolean;
  epoch: number;
  lastCleanup: CleanupResult | null;
  signIn: (householdId: string, role: "MEMBER" | "FACILITATOR", memberId?: string) => Promise<void>;
  recordConsent: (memberId: string, explained: boolean, given: boolean) => Promise<void>;
  switchProfile: (memberId: string) => Promise<string>;
  endSession: (reason: "USER_LOGOUT" | "FACILITATOR_HANDOVER" | "TIMEOUT" | "ERROR_RECOVERY") => Promise<CleanupResult>;
  refresh: () => Promise<void>;
  clearCleanup: () => void;
}

const SessionContext = createContext<SessionValue | null>(null);

function withoutToken(payload: SessionPayload): SessionPayload {
  const { token: _token, ...rest } = payload;
  return rest as SessionPayload;
}

export function SessionProvider({ children }: { children: ReactNode }) {
  const [session, setSessionState] = useState<SessionPayload | null>(null);
  const [ready] = useState(true);
  const [epoch, setEpoch] = useState(0);
  const [lastCleanup, setLastCleanup] = useState<CleanupResult | null>(null);
  const timer = useRef<number | null>(null);

  const clearPrivateState = useCallback(() => {
    setSessionToken(null);
    setSessionState(null);
    setEpoch((value) => value + 1);
  }, []);

  useEffect(() => {
    onUnauthorized(() => {
      clearPrivateState();
    });
    return () => onUnauthorized(null);
  }, [clearPrivateState]);

  useEffect(() => {
    if (timer.current) window.clearTimeout(timer.current);
    if (!session) return;
    const expires = new Date(session.expires_at).getTime();
    const delay = Math.max(expires - Date.now(), 0);
    // Cap at 10 minutes so a renewed server-side expiry is re-checked.
    timer.current = window.setTimeout(() => {
      clearPrivateState();
    }, Math.min(Math.max(delay, 0), 600_000));
    return () => {
      if (timer.current) window.clearTimeout(timer.current);
    };
  }, [session, clearPrivateState]);

  const signIn = useCallback(async (householdId: string, role: "MEMBER" | "FACILITATOR", memberId?: string) => {
    const payload = await api.startSession({
      household_id: householdId,
      role,
      member_id: role === "MEMBER" ? memberId : null,
      purpose: role === "FACILITATOR" ? "ASSISTED_SERVICE" : "MEMBER_SELF_SERVICE",
      facilitator_device: role === "FACILITATOR" ? "shared-demo-device-01" : undefined,
    });
    if (payload.token) setSessionToken(payload.token);
    setSessionState(withoutToken(payload));
    setLastCleanup(null);
    setEpoch((value) => value + 1);
  }, []);

  const refresh = useCallback(async () => {
    const payload = await api.currentSession();
    setSessionState(withoutToken(payload));
  }, []);

  const recordConsent = useCallback(
    async (memberId: string, explained: boolean, given: boolean) => {
      await api.consent({ member_id: memberId, consent_explained: explained, consent_given: given });
      await refresh();
      setEpoch((value) => value + 1);
    },
    [refresh],
  );

  const switchProfile = useCallback(async (memberId: string) => {
    const payload = await api.switchProfile(memberId);
    if (payload.token) setSessionToken(payload.token);
    setSessionState(withoutToken(payload));
    setEpoch((value) => value + 1);
    return payload.cleanup_notice;
  }, []);

  const endSession = useCallback(
    async (reason: "USER_LOGOUT" | "FACILITATOR_HANDOVER" | "TIMEOUT" | "ERROR_RECOVERY") => {
      let result: CleanupResult;
      try {
        result = await api.endSession({ reason, client_cleanup_confirmed: true });
      } catch {
        result = {
          session_id: "unknown",
          ended: true,
          ended_reason: reason,
          server_cleanup_verified: false,
          server_actions: ["Local session token discarded"],
          client_actions_required: [],
          limitations: [
            "The server could not confirm cleanup because the connection failed. The local token was discarded.",
          ],
        };
      }
      clearPrivateState();
      setLastCleanup(result);
      return result;
    },
    [clearPrivateState],
  );

  const value = useMemo<SessionValue>(
    () => ({
      session,
      ready,
      epoch,
      lastCleanup,
      signIn,
      recordConsent,
      switchProfile,
      endSession,
      refresh,
      clearCleanup: () => setLastCleanup(null),
    }),
    [session, ready, epoch, lastCleanup, signIn, recordConsent, switchProfile, endSession, refresh],
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession(): SessionValue {
  const value = useContext(SessionContext);
  if (!value) throw new Error("useSession must be used inside SessionProvider");
  return value;
}
