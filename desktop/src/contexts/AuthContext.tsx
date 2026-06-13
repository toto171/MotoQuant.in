// MotoQuant Pro desktop — Auth + licensing context.
// ==================================================
// The desktop app is a LICENSED CLIENT of the hosted MotoQuant API. The whole
// app is gated behind a valid authenticated session: an unauthenticated user
// sees the login screen, never the simulator. All valuable compute (physics
// engine, optimizer, surrogate, catalog) lives server-side, so a copied or
// patched client is worthless without a live licensed session against the
// operator's server.
//
// IMPORTANT — the client does NOT and CANNOT enforce its own license. Device
// binding, tier, and revocation are SERVER-AUTHORITATIVE. This context only
// presents credentials and reacts to the server's verdict (401 → re-login,
// 402/403 → upgrade prompt).
//
// Token storage (honest about the trade-off):
//   • access token  → React state only (in-memory; never persisted to disk)
//   • refresh token → OS keychain (macOS Keychain / Windows Credential Manager
//                     / Linux Secret Service) via the Rust `keychain_*`
//                     commands, with a sessionStorage fallback for dev/browser
//                     or a keychain-less runtime (see lib/secureStore.ts).
// The refresh token never touches plaintext disk in the packaged app. This is
// the hardening step previously flagged in desktop/SECURITY.md "Residual risk".

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { api, registerAuthHooks } from "@/lib/api";
import type { MeResponse, TokenPair } from "@/types/api";
import { getSecret, setSecret } from "@/lib/secureStore";

const REFRESH_KEY = "mq_refresh";

interface AuthContextValue {
  user: MeResponse | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  tier: string | null;
  applyTokens: (data: TokenPair) => void;
  loginPassword: (email: string, password: string) => Promise<void>;
  registerPassword: (email: string, password: string) => Promise<void>;
  verifyMagicLink: (token: string) => Promise<void>;
  logout: () => Promise<void>;
  refetchUser: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

// Refresh-token persistence is delegated to the OS keychain (with a
// sessionStorage fallback) — see lib/secureStore.ts. readRefresh is async
// (keychain access is async); writeRefresh is fire-and-forget: the in-memory
// access token already drives the live session, so persistence completing a
// tick later is harmless.
function readRefresh(): Promise<string | null> {
  return getSecret(REFRESH_KEY);
}
function writeRefresh(token: string | null): void {
  void setSecret(REFRESH_KEY, token);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<MeResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Access token lives only in a ref (in-memory). Never persisted.
  const accessTokenRef = useRef<string | null>(null);
  // Guards against concurrent refreshes (multiple 401s racing).
  const refreshPromiseRef = useRef<Promise<string | null> | null>(null);

  const clearAuth = useCallback(() => {
    accessTokenRef.current = null;
    writeRefresh(null);
    setUser(null);
  }, []);

  const fetchMe = useCallback(async () => {
    try {
      const me = await api.authMe();
      setUser(me);
    } catch {
      // /me failed even after refresh — treat as signed out.
      clearAuth();
    }
  }, [clearAuth]);

  const applyTokens = useCallback((data: TokenPair) => {
    accessTokenRef.current = data.access_token;
    writeRefresh(data.refresh_token);
  }, []);

  // Single-flight silent refresh. Returns a fresh access token or null.
  const refreshAccessToken = useCallback(async (): Promise<string | null> => {
    if (refreshPromiseRef.current) return refreshPromiseRef.current;
    const refresh = await readRefresh();
    if (!refresh) return null;

    refreshPromiseRef.current = (async () => {
      try {
        const data = await api.authRefresh(refresh);
        accessTokenRef.current = data.access_token;
        writeRefresh(data.refresh_token);
        return data.access_token;
      } catch {
        clearAuth();
        return null;
      } finally {
        refreshPromiseRef.current = null;
      }
    })();
    return refreshPromiseRef.current;
  }, [clearAuth]);

  // Register the fetch-layer hooks so api.ts can attach the token + refresh.
  useEffect(() => {
    registerAuthHooks({
      getAccessToken: () => accessTokenRef.current,
      refreshAccessToken,
      onAuthExpired: () => clearAuth(),
    });
    return () => registerAuthHooks(null);
  }, [refreshAccessToken, clearAuth]);

  // On mount: try to restore a session from the refresh token.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      const fresh = await refreshAccessToken();
      if (!cancelled) {
        if (fresh) await fetchMe();
        setIsLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [refreshAccessToken, fetchMe]);

  const loginPassword = useCallback(
    async (email: string, password: string) => {
      const data = await api.authLogin(email, password);
      applyTokens(data);
      await fetchMe();
    },
    [applyTokens, fetchMe],
  );

  const registerPassword = useCallback(
    async (email: string, password: string) => {
      const data = await api.authRegister(email, password);
      applyTokens(data);
      await fetchMe();
    },
    [applyTokens, fetchMe],
  );

  const verifyMagicLink = useCallback(
    async (token: string) => {
      const data = await api.authVerifyMagicLink(token);
      applyTokens(data);
      await fetchMe();
    },
    [applyTokens, fetchMe],
  );

  const logout = useCallback(async () => {
    try {
      await api.authLogout();
    } catch {
      /* best-effort server-side logout */
    }
    clearAuth();
  }, [clearAuth]);

  const value: AuthContextValue = {
    user,
    isAuthenticated: !!user,
    isLoading,
    tier: user?.tier ?? null,
    applyTokens,
    loginPassword,
    registerPassword,
    verifyMagicLink,
    logout,
    refetchUser: () => {
      void fetchMe();
    },
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
