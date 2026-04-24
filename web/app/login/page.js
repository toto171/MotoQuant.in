"use client";

/**
 * MotoQuant Pro — Login Page
 * ===========================
 * Passwordless magic-link sign-in.
 * Step 1: user enters email → POST /api/auth/magic-link
 * Step 2: user clicks link in email → /login?token=... → POST /api/auth/verify
 */

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "../../components/AuthProvider";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "https://web-production-de6eb.up.railway.app";

export default function LoginPage() {
  const router = useRouter();
  const params = useSearchParams();
  const { isAuthenticated, applyLoginTokens } = useAuth();

  const [email, setEmail] = useState("");
  const [status, setStatus] = useState("idle"); // idle | sending | sent | verifying | error
  const [errorMsg, setErrorMsg] = useState("");
  const [devToken, setDevToken] = useState(""); // visible in dev mode

  // ── If already logged in, redirect to account ──────────────────────────────
  useEffect(() => {
    if (isAuthenticated) router.replace("/account");
  }, [isAuthenticated, router]);

  // ── If token in query string, auto-verify ─────────────────────────────────
  useEffect(() => {
    const token = params.get("token");
    if (token && status === "idle") {
      verifyToken(token);
    }
  }, [params]); // eslint-disable-line react-hooks/exhaustive-deps

  async function verifyToken(token) {
    setStatus("verifying");
    try {
      const res = await fetch(`${API_BASE}/api/auth/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Invalid or expired sign-in link.");
      }
      const data = await res.json();
      applyLoginTokens(data);
      router.replace("/account");
    } catch (err) {
      setStatus("error");
      setErrorMsg(err.message || "Verification failed. Please try again.");
    }
  }

  async function requestLink(e) {
    e.preventDefault();
    if (!email.trim()) return;
    setStatus("sending");
    setErrorMsg("");
    try {
      const res = await fetch(`${API_BASE}/api/auth/magic-link`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim() }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Failed to send sign-in link.");
      }
      setStatus("sent");
      if (data.dev_token) setDevToken(data.dev_token); // dev only
    } catch (err) {
      setStatus("error");
      setErrorMsg(err.message);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-gray-950 px-4">
      <div className="w-full max-w-sm space-y-8">
        {/* Logo */}
        <div className="text-center">
          <a href="/" className="text-2xl font-extrabold tracking-tight text-white">
            Moto<span className="text-orange-500">Quant</span>
          </a>
          <p className="mt-1 text-sm text-gray-400">The physics of faster.</p>
        </div>

        {/* Card */}
        <div className="rounded-2xl bg-gray-900 border border-gray-800 p-8 shadow-xl">
          {status === "verifying" && (
            <div className="text-center text-gray-300">
              <div className="mb-4 text-4xl">🔑</div>
              <p className="font-medium">Verifying your sign-in link…</p>
            </div>
          )}

          {status === "sent" && (
            <div className="text-center text-gray-200">
              <div className="mb-4 text-4xl">📬</div>
              <h2 className="text-lg font-semibold">Check your inbox</h2>
              <p className="mt-2 text-sm text-gray-400">
                We sent a sign-in link to <strong>{email}</strong>.
                It expires in 10 minutes.
              </p>
              {devToken && (
                <div className="mt-4 rounded-lg bg-yellow-900/40 border border-yellow-700 p-3 text-left">
                  <p className="text-xs text-yellow-400 font-mono font-bold">DEV TOKEN</p>
                  <p className="mt-1 text-xs text-yellow-300 break-all font-mono">{devToken}</p>
                  <button
                    onClick={() => verifyToken(devToken)}
                    className="mt-2 rounded bg-yellow-600 px-3 py-1 text-xs font-semibold text-white hover:bg-yellow-500"
                  >
                    Auto-verify (dev only)
                  </button>
                </div>
              )}
              <button
                onClick={() => { setStatus("idle"); setDevToken(""); }}
                className="mt-6 text-sm text-orange-400 underline hover:text-orange-300"
              >
                Try a different email
              </button>
            </div>
          )}

          {(status === "idle" || status === "sending" || status === "error") && (
            <>
              <h2 className="text-lg font-semibold text-white">Sign in</h2>
              <p className="mt-1 text-sm text-gray-400">
                No password needed — we'll email you a sign-in link.
              </p>

              {status === "error" && (
                <div className="mt-4 rounded-lg bg-red-900/40 border border-red-700 px-4 py-3 text-sm text-red-300">
                  {errorMsg}
                </div>
              )}

              <form onSubmit={requestLink} className="mt-6 space-y-4">
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-gray-300">
                    Email address
                  </label>
                  <input
                    id="email"
                    type="email"
                    autoComplete="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@example.com"
                    className="mt-1 block w-full rounded-lg border border-gray-700 bg-gray-800
                               px-4 py-2.5 text-white placeholder-gray-500
                               focus:border-orange-500 focus:outline-none focus:ring-1
                               focus:ring-orange-500 text-sm"
                  />
                </div>
                <button
                  type="submit"
                  disabled={status === "sending"}
                  className="w-full rounded-lg bg-orange-500 py-2.5 text-sm font-semibold
                             text-white shadow hover:bg-orange-600 disabled:opacity-50
                             disabled:cursor-not-allowed transition-colors"
                >
                  {status === "sending" ? "Sending…" : "Send sign-in link"}
                </button>
              </form>

              <p className="mt-6 text-center text-xs text-gray-500">
                By signing in you agree to our{" "}
                <a href="/terms" className="underline hover:text-gray-300">Terms</a> and{" "}
                <a href="/privacy" className="underline hover:text-gray-300">Privacy Policy</a>.
              </p>
            </>
          )}
        </div>

        <p className="text-center text-xs text-gray-600">
          New to MotoQuant?{" "}
          <a href="/pricing" className="text-orange-400 underline hover:text-orange-300">
            See plans →
          </a>
        </p>
      </div>
    </main>
  );
}
