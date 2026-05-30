"use client";

/**
 * MotoQuant Pro — Auth Context Provider
 * =======================================
 * Manages JWT access/refresh tokens in memory (never localStorage).
 * Exposes useAuth() hook to all child components.
 *
 * Token storage strategy
 * ----------------------
 * - Access token: React state (in-memory, lost on page reload → auto-refreshed)
 * - Refresh token: httpOnly-equivalent: stored in React state + sessionStorage
 *   for tab persistence. NOT localStorage (XSS risk).
 * - On mount: checks sessionStorage for a refresh token, exchanges it for a
 *   new access token silently.
 *
 * Usage
 * -----
 *   // In layout.js:
 *   <AuthProvider><App /></AuthProvider>
 *
 *   // In any component:
 *   const { user, login, logout, isLoading } = useAuth();
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "https://motoquant-api.onrender.com";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);       // { id, email, tier, subscription_status, license_keys }
  const [accessToken, setAccessToken] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const refreshTimerRef = useRef(null);

  // ── helpers ────────────────────────────────────────────────────────────────

  const _clearAuth = useCallback(() => {
    setUser(null);
    setAccessToken(null);
    sessionStorage.removeItem("mq_refresh");
    if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current);
  }, []);

  const _scheduleRefresh = useCallback((expiresInMs) => {
    if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current);
    // Refresh 60 s before expiry (access token TTL = 15 min)
    const delay = Math.max(expiresInMs - 60_000, 30_000);
    refreshTimerRef.current = setTimeout(() => {
      _silentRefresh();
    }, delay);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const _silentRefresh = useCallback(async () => {
    const refreshToken = sessionStorage.getItem("mq_refresh");
    if (!refreshToken) {
      _clearAuth();
      setIsLoading(false);
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/api/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      if (!res.ok) {
        _clearAuth();
        setIsLoading(false);
        return;
      }
      const data = await res.json();
      _applyTokens(data);
    } catch {
      _clearAuth();
    } finally {
      setIsLoading(false);
    }
  }, [_clearAuth]); // eslint-disable-line react-hooks/exhaustive-deps

  const _applyTokens = useCallback(
    (data) => {
      // data = { access_token, refresh_token, tier }
      setAccessToken(data.access_token);
      sessionStorage.setItem("mq_refresh", data.refresh_token);
      // Decode expiry from JWT (middle segment) to schedule refresh
      try {
        const payload = JSON.parse(atob(data.access_token.split(".")[1]));
        const expiresInMs = payload.exp * 1000 - Date.now();
        _scheduleRefresh(expiresInMs);
      } catch {
        _scheduleRefresh(14 * 60 * 1000); // fallback: 14 min
      }
    },
    [_scheduleRefresh]
  );

  // ── fetch user profile ─────────────────────────────────────────────────────

  const fetchMe = useCallback(
    async (token) => {
      try {
        const res = await fetch(`${API_BASE}/api/auth/me`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) return;
        const me = await res.json();
        setUser(me);
      } catch {
        /* silently ignore — user stays null */
      }
    },
    []
  );

  // ── on mount: try silent refresh ───────────────────────────────────────────

  useEffect(() => {
    _silentRefresh();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ── whenever accessToken changes, load user profile ───────────────────────

  useEffect(() => {
    if (accessToken) fetchMe(accessToken);
  }, [accessToken, fetchMe]);

  // ── public API ────────────────────────────────────────────────────────────

  /**
   * Call after POST /api/auth/verify returns { access_token, refresh_token, tier }.
   */
  const applyLoginTokens = useCallback(
    (data) => {
      _applyTokens(data);
    },
    [_applyTokens]
  );

  const logout = useCallback(async () => {
    if (accessToken) {
      try {
        await fetch(`${API_BASE}/api/auth/logout`, {
          method: "POST",
          headers: { Authorization: `Bearer ${accessToken}` },
        });
      } catch {
        /* best-effort */
      }
    }
    _clearAuth();
    setIsLoading(false);
  }, [accessToken, _clearAuth]);

  const value = {
    user,
    accessToken,
    isLoading,
    isAuthenticated: !!user,
    applyLoginTokens,
    logout,
    refetchUser: () => accessToken && fetchMe(accessToken),
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}

/**
 * Returns the Authorization header object for fetch calls.
 * Usage: fetch(url, { headers: { ...useAuthHeader() } })
 */
export function useAuthHeader() {
  const { accessToken } = useAuth();
  return accessToken ? { Authorization: `Bearer ${accessToken}` } : {};
}
