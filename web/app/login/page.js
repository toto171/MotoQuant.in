"use client";

/**
 * MotoQuant Pro — Login / Register Page
 * ======================================
 * Three modes on one surface:
 *   - "signin"   email + password (works with zero external services)
 *   - "register" create account (auto-signs-in on success)
 *   - "magic"    passwordless magic-link (also the forgot-password path;
 *                emails send once SMTP/RESEND env vars are set server-side)
 * Arriving with ?token=... verifies a magic link.
 * Arriving with ?signup=1 opens register mode.
 * ?next=/path is honoured after auth (same-origin paths only).
 *
 * IGNITION v5 (July 2026): single centered `.card` on asphalt, mode tabs as
 * `.chip` toggles (accent orange when active), `.input-base` fields,
 * `.label-mono` labels, magic-link sent state on `.chip-go`. The submit
 * stays an ActionButton + useAsyncTask (staged progress, cold-start caption
 * for free) and the ?token= verification shows a staged SimProgress bar.
 * Auth flows + EXP-007 unchanged.
 */

import { Suspense, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { AlertCircle } from "lucide-react";
import { useAuth } from "../../components/AuthProvider";
import SiteNav from "../../components/SiteNav";
import SiteFooter from "../../components/SiteFooter";
import CodeComment from "../../components/CodeComment";
import SimProgress from "../../components/SimProgress";
import ActionButton from "../../components/ActionButton";
import { SkeletonCard } from "../../components/Skeleton";
import useAsyncTask from "../../lib/useAsyncTask";
import { track } from "../../lib/telemetry";

import { API_URL_DIRECT as API_BASE } from "../../lib/api";

function LoginPageInner() {
  const router = useRouter();
  const params = useSearchParams();
  const { isAuthenticated, applyLoginTokens } = useAuth();

  const formRef = useRef(null);
  const [mode, setMode] = useState(
    params?.get("signup") === "1" ? "register" : "signin"
  );
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [password2, setPassword2] = useState("");
  // "idle" (form) | "sent" (magic link dispatched) | "verifying" (?token=) |
  // "error" (verification failed — form shows with the error box).
  // Form-submit progress/errors live on submitTask.
  const [status, setStatus] = useState("idle");
  const [errorMsg, setErrorMsg] = useState("");
  const [devToken, setDevToken] = useState("");

  // GROWTH_EXP_007: A/B variant — see data/growth_experiments.json
  const ctaVariant = params?.get("variant") === "B" ? "B" : "A";
  const sendButtonLabel =
    ctaVariant === "B" ? "Start free · email me the link" : "Send sign-in link";

  // Same-origin ?next= redirect (defends against open-redirect abuse).
  // Must be a clean absolute path: starts with a single "/", and no "//" or
  // backslash — browsers normalise "\" to "/", so "/\evil.com" would otherwise
  // become the protocol-relative "//evil.com" and redirect off-site.
  const nextPath = (() => {
    const n = params?.get("next") || "";
    const safe =
      n.startsWith("/") &&
      !n.startsWith("//") &&
      !n.includes("\\") &&
      !n.includes("://");
    return safe ? n : "/account";
  })();

  useEffect(() => {
    if (isAuthenticated) router.replace(nextPath);
  }, [isAuthenticated, router, nextPath]);

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
      router.replace(nextPath);
    } catch (err) {
      setStatus("error");
      setErrorMsg(err.message || "Verification failed. Please try again.");
    }
  }

  // One task for the whole three-mode form — only one mode is visible at a
  // time, so a single active flag maps 1:1 onto the single submit button.
  const submitTask = useAsyncTask(async (signal) => {
    setErrorMsg("");
    if (mode === "magic") {
      const res = await fetch(`${API_BASE}/api/auth/magic-link`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim() }),
        signal,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to send sign-in link.");
      setStatus("sent");
      if (data.dev_token) setDevToken(data.dev_token);
      return data;
    }
    if (mode === "register") {
      if (password.length < 8) {
        throw new Error("Password must be at least 8 characters.");
      }
      if (password !== password2) {
        throw new Error("Passwords don't match.");
      }
    }
    const endpoint = mode === "register" ? "register" : "login";
    const res = await fetch(`${API_BASE}/api/auth/${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: email.trim(), password }),
      signal,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const detail =
        typeof data.detail === "string"
          ? data.detail
          : data.detail?.[0]?.msg || "Sign-in failed. Please try again.";
      throw new Error(detail);
    }
    applyLoginTokens(data);
    if (mode === "register") {
      track("signup_completed", { method: "password" });
    }
    router.replace(nextPath);
    return data;
  });

  function handleSubmit(e) {
    e.preventDefault();
    if (!submitTask.active) submitTask.run();
  }

  function switchMode(next) {
    setMode(next);
    setStatus("idle");
    setErrorMsg("");
    setPassword("");
    setPassword2("");
    submitTask.reset();
  }

  const headings = {
    signin: ["Sign in to the strip", "Welcome back — pick up where you left off."],
    register: ["Create your account", "Start free — 30 sims a day on the full 541-bike catalog. No card required."],
    magic: ["Magic-link sign-in", "No password needed — we’ll email you a sign-in link."],
  };
  const [heading, subheading] = headings[mode];
  const formError = (status === "error" ? errorMsg : "") || submitTask.error;

  const tabClass = (m) =>
    [
      "chip h-10 flex-1 justify-center whitespace-nowrap transition-colors",
      mode === m
        ? "chip-volt"
        : "border-transparent text-white/45 hover:text-white",
    ].join(" ");

  const quietLink =
    "text-white/60 underline decoration-white/25 underline-offset-2 hover:text-white transition-colors";

  return (
    <div className="min-h-screen bg-asphalt-0 text-white">
      <SiteNav />
      <main
        id="main"
        className="flex min-h-[calc(100vh-4rem)] items-center justify-center px-4 pt-24 pb-16"
      >
        <div className="w-full max-w-md space-y-6">
          <div className="text-center space-y-3">
            <CodeComment center>account access</CodeComment>
            <p className="font-display font-bold text-2xl tracking-tight text-white">
              The physics of <span className="text-accent">faster</span>
            </p>
          </div>

          <div className="card p-6 sm:p-8">
            {status === "verifying" && (
              <div className="py-4 text-center">
                <span className="chip chip-stage">Verifying</span>
                <p className="mt-4 mb-4 font-display font-semibold text-lg md:text-xl text-white">
                  Verifying your sign-in link
                </p>
                <SimProgress
                  active
                  progress={null}
                  label="Verifying your sign-in link"
                  className="text-left"
                />
              </div>
            )}

            {status === "sent" && (
              <div className="text-center">
                <span className="chip chip-go">Link sent</span>
                <h2 className="mt-4 font-display font-bold text-2xl tracking-tight text-white">
                  Check your inbox
                </h2>
                <p className="mt-3 text-sm text-white/65">
                  We sent a sign-in link to{" "}
                  <strong className="font-medium text-white">{email}</strong>.
                  It expires in 10 minutes.
                </p>
                {devToken && (
                  <div className="mt-5 rounded-lg border border-signal-stage/30 bg-signal-stage/10 p-3 text-left">
                    <p className="label-mono text-signal-stage">Dev token</p>
                    <p className="mt-1 break-all font-mono text-xs text-signal-stage/80">{devToken}</p>
                    <button
                      onClick={() => verifyToken(devToken)}
                      className="mt-2 rounded bg-signal-stage px-3 py-1 text-xs font-semibold text-asphalt-0 hover:bg-signal-stage/85 transition-colors"
                    >
                      Auto-verify (dev only)
                    </button>
                  </div>
                )}
                <button
                  onClick={() => { setStatus("idle"); setDevToken(""); submitTask.reset(); }}
                  className={`mt-6 text-sm ${quietLink}`}
                >
                  Try a different email
                </button>
              </div>
            )}

            {(status === "idle" || status === "error") && (
              <>
                <div className="mb-6 flex gap-1.5" role="tablist" aria-label="Sign-in method">
                  <button onClick={() => switchMode("signin")} className={tabClass("signin")}>
                    Sign in
                  </button>
                  <button onClick={() => switchMode("register")} className={tabClass("register")}>
                    Register
                  </button>
                  <button onClick={() => switchMode("magic")} className={tabClass("magic")}>
                    Magic link
                  </button>
                </div>

                <h2 className="font-display font-bold text-2xl tracking-tight text-white">
                  {heading}
                </h2>
                <p className="mt-2 text-sm text-white/65">{subheading}</p>

                {formError && (
                  <div className="mt-5 flex items-start gap-2 rounded-lg border border-signal-foul/40 bg-signal-foul/10 px-4 py-3 text-sm text-signal-foul">
                    <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                    <span>{formError}</span>
                  </div>
                )}

                <form ref={formRef} onSubmit={handleSubmit} className="mt-6 space-y-4">
                  <div>
                    <label htmlFor="email" className="mb-2 block label-mono">
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
                      className="input-base font-mono"
                    />
                  </div>

                  {mode !== "magic" && (
                    <div>
                      <label htmlFor="password" className="mb-2 block label-mono">
                        Password
                      </label>
                      <input
                        id="password"
                        type="password"
                        autoComplete={mode === "register" ? "new-password" : "current-password"}
                        required
                        minLength={mode === "register" ? 8 : 1}
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder={mode === "register" ? "At least 8 characters" : "Your password"}
                        className="input-base font-mono"
                      />
                    </div>
                  )}

                  {mode === "register" && (
                    <div>
                      <label htmlFor="password2" className="mb-2 block label-mono">
                        Confirm password
                      </label>
                      <input
                        id="password2"
                        type="password"
                        autoComplete="new-password"
                        required
                        minLength={8}
                        value={password2}
                        onChange={(e) => setPassword2(e.target.value)}
                        placeholder="Same password again"
                        className="input-base font-mono"
                      />
                    </div>
                  )}

                  {/* hidden submit keeps Enter-to-submit working (ActionButton is type=button) */}
                  <input type="submit" hidden />
                  <div
                    data-exp={mode === "magic" ? "EXP-007" : undefined}
                    data-variant={mode === "magic" ? ctaVariant : undefined}
                  >
                    <ActionButton
                      task={submitTask}
                      onRun={() => formRef.current?.requestSubmit()}
                      label={
                        mode === "magic"
                          ? sendButtonLabel
                          : mode === "register"
                            ? "Create free account"
                            : "Sign in"
                      }
                      runningLabel={
                        mode === "magic"
                          ? "Sending link"
                          : mode === "register"
                            ? "Creating account"
                            : "Signing in"
                      }
                      className="w-full"
                    />
                  </div>
                </form>

                {mode === "signin" && (
                  <button
                    onClick={() => switchMode("magic")}
                    className={`mt-4 text-xs ${quietLink}`}
                  >
                    Forgot password? Sign in with a magic link instead →
                  </button>
                )}

                <p className="mt-6 text-center text-xs text-white/40">
                  By signing in you agree to our{" "}
                  <a href="/terms" className={quietLink}>Terms</a>{" "}
                  and{" "}
                  <a href="/privacy" className={quietLink}>Privacy Policy</a>.
                </p>
              </>
            )}
          </div>

          <p className="text-center text-xs text-white/45">
            {mode === "register" ? (
              <>
                Already racing with us?{" "}
                <button onClick={() => switchMode("signin")} className={quietLink}>
                  Sign in →
                </button>
              </>
            ) : (
              <>
                New to MotoQuant?{" "}
                <button onClick={() => switchMode("register")} className={quietLink}>
                  Create a free account →
                </button>
              </>
            )}
          </p>
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-asphalt-0 px-4">
          <div className="w-full max-w-md">
            <SkeletonCard rows={4} />
          </div>
        </div>
      }
    >
      <LoginPageInner />
    </Suspense>
  );
}
