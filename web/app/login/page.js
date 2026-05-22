"use client";

/**
 * MotoQuant Pro — Login Page
 * ===========================
 * Passwordless magic-link sign-in.
 * Step 1: user enters email → POST /api/auth/magic-link
 * Step 2: user clicks link in email → /login?token=... → POST /api/auth/verify
 *
 * Direction A refit (April 2026): SiteNav + black canvas + brand-orange
 * accents. Magic-link flow + AuthProvider integration unchanged.
 */

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Mail, KeyRound, AlertCircle } from "lucide-react";
import { useAuth } from "../../components/AuthProvider";
import SiteNav from "../../components/SiteNav";
import SiteFooter from "../../components/SiteFooter";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "https://web-production-de6eb.up.railway.app";

function LoginPageInner() {
  const router = useRouter();
  const params = useSearchParams();
  const { isAuthenticated, applyLoginTokens } = useAuth();

  const [email, setEmail] = useState("");
  const [status, setStatus] = useState("idle");
  const [errorMsg, setErrorMsg] = useState("");
  const [devToken, setDevToken] = useState("");

  // GROWTH_EXP_007: A/B variant — see data/growth_experiments.json
  // Default OFF (control). Visitors who land with ?variant=B see the
  // value-forward, zero-friction CTA copy. Same form action, same href,
  // same heading, same canonical URL, same SEO. Button text only.
  const ctaVariant = params?.get("variant") === "B" ? "B" : "A";
  const sendButtonLabel =
    ctaVariant === "B" ? "Start free · email me the link" : "Send sign-in link";

  useEffect(() => {
    if (isAuthenticated) router.replace("/account");
  }, [isAuthenticated, router]);

  useEffect(() => {
    const token = params.get("token");
    if (token && status === "idle") verifyToken(token);
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
      if (!res.ok) throw new Error(data.detail || "Failed to send sign-in link.");
      setStatus("sent");
      if (data.dev_token) setDevToken(data.dev_token);
    } catch (err) {
      setStatus("error");
      setErrorMsg(err.message);
    }
  }

  return (
    <div className="min-h-screen bg-black text-white">
      <SiteNav />
      <main className="flex min-h-[calc(100vh-4rem)] items-center justify-center px-4 pt-20 pb-12">
        <div className="w-full max-w-sm space-y-8">
          <div className="text-center">
            <p className="font-mono text-[10px] text-brand-orange uppercase tracking-[0.3em]">
              The physics of faster
            </p>
          </div>

          <div className="rounded-2xl bg-ink-1/70 border border-white/10 p-8 shadow-2xl">
            {status === "verifying" && (
              <div className="text-center text-white/85">
                <KeyRound className="w-8 h-8 mx-auto text-brand-orange mb-3" />
                <p className="font-display font-bold text-lg">Verifying your sign-in link…</p>
                <p className="mt-2 text-sm text-white/55">Hang tight, this takes a second.</p>
              </div>
            )}

            {status === "sent" && (
              <div className="text-center text-white/85">
                <Mail className="w-8 h-8 mx-auto text-brand-orange mb-3" />
                <h2 className="font-display font-bold text-xl text-white">Check your inbox</h2>
                <p className="mt-3 text-sm text-white/60">
                  We sent a sign-in link to <strong className="text-white">{email}</strong>.
                  It expires in 10 minutes.
                </p>
                {devToken && (
                  <div className="mt-5 rounded-lg bg-amber-900/25 border border-amber-500/30 p-3 text-left">
                    <p className="text-xs text-amber-400 font-mono font-bold tracking-wider">DEV TOKEN</p>
                    <p className="mt-1 text-xs text-amber-200/85 break-all font-mono">{devToken}</p>
                    <button
                      onClick={() => verifyToken(devToken)}
                      className="mt-2 rounded bg-amber-600 px-3 py-1 text-xs font-semibold text-black hover:bg-amber-500 transition-colors"
                    >
                      Auto-verify (dev only)
                    </button>
                  </div>
                )}
                <button
                  onClick={() => { setStatus("idle"); setDevToken(""); }}
                  className="mt-6 text-sm text-brand-accent hover:text-white transition-colors"
                >
                  Try a different email
                </button>
              </div>
            )}

            {(status === "idle" || status === "sending" || status === "error") && (
              <>
                <h2 className="font-display font-bold text-2xl text-white">Sign in</h2>
                <p className="mt-1 text-sm text-white/55">
                  No password needed — we&rsquo;ll email you a sign-in link.
                </p>

                {status === "error" && (
                  <div className="mt-5 rounded-lg bg-red-900/25 border border-red-500/40 px-4 py-3 text-sm text-red-200 flex items-start gap-2">
                    <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                    <span>{errorMsg}</span>
                  </div>
                )}

                <form onSubmit={requestLink} className="mt-6 space-y-4">
                  <div>
                    <label htmlFor="email" className="block text-[11px] font-mono text-white/55 uppercase tracking-widest mb-2">
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
                      className="block w-full rounded-md border border-white/10 bg-black/40 px-4 py-3 text-white placeholder-white/30 focus:border-brand-orange focus:outline-none focus:ring-1 focus:ring-brand-orange text-sm font-mono transition-colors"
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={status === "sending"}
                    data-exp="EXP-007"
                    data-variant={ctaVariant}
                    className="w-full rounded-md bg-brand-orange py-3 text-sm font-display font-bold text-black shadow-orange-soft hover:bg-brand-orangeLight disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {status === "sending" ? "Sending…" : sendButtonLabel}
                  </button>
                </form>

                <p className="mt-6 text-center text-xs text-white/40">
                  By signing in you agree to our{" "}
                  <a href="/terms" className="text-brand-accent hover:text-white transition-colors">Terms</a>{" "}
                  and{" "}
                  <a href="/privacy" className="text-brand-accent hover:text-white transition-colors">Privacy Policy</a>.
                </p>
              </>
            )}
          </div>

          <p className="text-center text-xs text-white/45">
            New to MotoQuant?{" "}
            <a href="/pricing" className="text-brand-orange hover:text-brand-orangeLight transition-colors">
              See plans →
            </a>
          </p>
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-black flex items-center justify-center text-white/55 font-mono text-sm">Loading…</div>}>
      <LoginPageInner />
    </Suspense>
  );
}
