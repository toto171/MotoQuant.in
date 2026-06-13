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
//   • refresh token → sessionStorage (cleared when the app closes; NOT
//                     localStorage, which would survive restarts and widen the
//                     XSS exfiltration window)
// A future hardening step is to move the refresh token into the OS keychain via
// a Tauri secure-store plugin — see desktop/SECURITY.md "Residual risk". We
// deliberately avoid persisting the refresh token to plaintext disk.

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

function readRefresh(): string | null {
  try {
    return sessionStorage.getItem(REFRESH_KEY);
  } catch {
    return null;
  }
}
function writeRefresh(token: string | null): void {
  try {
    if (token) sessionStorage.setItem(REFRESH_KEY, token);
    else sessionStorage.removeItem(REFRESH_KEY);
  } catch {
    /* sessionStorage unavailable — degrade to in-memory-only session */
  }
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
    const refresh = readRefresh();
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
