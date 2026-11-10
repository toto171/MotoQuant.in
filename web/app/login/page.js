"use client";

/**
 * MotoQuant — Login / Register Page
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
 * v6 (CLARITY): one clear primary form (email + password) with two quiet
 * secondary choices — "Create an account" and "Email me a sign-in link
 * instead". All flows still hit the same endpoints; submit stays an
 * ActionButton + useAsyncTask, ?token= verification shows a staged
 * SimProgress bar.
 */

import { Suspense, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { AlertCircle } from "lucide-react";
import { useAuth } from "../../components/AuthProvider";
import SiteNav from "../../components/SiteNav";
import SiteFooter from "../../components/SiteFooter";
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

  const sendButtonLabel = "Email me a sign-in link";

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
        throw new Error(
          typeof err.detail === "string" ? err.detail : "That sign-in link is invalid or has expired. Request a new one."
        );
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
   try {
    setErrorMsg("");
    if (mode === "magic") {
      const res = await fetch(`${API_BASE}/api/auth/magic-link`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim() }),
        signal,
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(typeof data.detail === "string" ? data.detail : "We couldn't send the sign-in link. Check the email address and try again.");
      setStatus("sent");
      if (data.dev_token) setDevToken(data.dev_token);
      return data;
    }
    if (mode === "register") {
      if (password.length < 8) {
        throw new Error("Choose a password with at least 8 characters.");
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
          : data.detail?.[0]?.msg || "We couldn't sign you in. Please try again.";
      throw new Error(
        res.status === 401 ? "That email and password don't match. Check them and try again." : detail
      );
    }
    applyLoginTokens(data);
    if (mode === "register") {
      track("signup_completed", { method: "password" });
    }
    router.replace(nextPath);
    return data;
   } catch (e) {
    if (e?.name === "AbortError") throw e;
    if (e instanceof TypeError) {
      throw new Error("We couldn't reach the server. It may be waking up, so try again in a few seconds.");
    }
    throw e;
   }
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
    signin: ["Sign in", "Sign in to save your runs. You don't need an account to use the simulator."],
    register: ["Create an account", "An account only lets you save your runs and find them again later."],
    magic: ["Email me a sign-in link", "No password needed. We'll email you a link that signs you in."],
  };
  const [heading, subheading] = headings[mode];
  const formError = (status === "error" ? errorMsg : "") || submitTask.error;

  const quietLink =
    "inline-flex min-h-[44px] items-center text-left text-white/70 underline decoration-white/30 underline-offset-2 hover:text-white transition-colors";

  return (
    <div className="min-h-screen bg-asphalt-0 text-white">
      <SiteNav />
      <main
        id="main"
        className="flex min-h-[calc(100vh-4rem)] items-start justify-center px-4 pt-28 pb-16 sm:items-center"
      >
        <div className="w-full max-w-md space-y-6">
          <div className="card p-6 sm:p-8">
            {status === "verifying" && (
              <div className="py-4 text-center">
                
                <p className="mb-4 font-display font-semibold text-lg md:text-xl text-white">
                  Checking your sign-in link
                </p>
                <SimProgress
                  active
                  progress={null}
                  label="Checking your sign-in link"
                  className="text-left"
                />
              </div>
            )}

            {status === "sent" && (
              <div className="text-center">
                
                <h2 className="font-display font-bold text-2xl tracking-tight text-white">
                  Check your email
                </h2>
                <p className="mt-3 text-sm text-white/65">
                  We sent a sign-in link to{" "}
                  <strong className="font-medium text-white">{email}</strong>.
                  The link works for 10 minutes. Check your spam folder if it doesn't arrive.
                </p>
                {devToken && (
                  <div className="mt-5 rounded-lg border border-signal-stage/30 bg-signal-stage/10 p-3 text-left">
                    <p className="text-sm font-medium text-signal-stage">Developer sign-in token</p>
                    <p className="mt-1 break-all font-mono text-xs text-signal-stage/80">{devToken}</p>
                    <button
                      type="button"
                      onClick={() => verifyToken(devToken)}
                      className="btn-ghost btn-sm mt-2"
                    >
                      Sign in with this token
                    </button>
                  </div>
                )}
                <button
                  type="button"
                  onClick={() => { setStatus("idle"); setDevToken(""); submitTask.reset(); }}
                  className={`mt-4 text-sm ${quietLink}`}
                >
                  Use a different email
                </button>
              </div>
            )}

            {(status === "idle" || status === "error") && (
              <>
                <h2 className="font-display font-bold text-2xl tracking-tight text-white">
                  {heading}
                </h2>
                <p className="mt-2 text-sm text-white/65">{subheading}</p>

                {formError && (
                  <div role="alert" className="mt-5 flex items-start gap-2 rounded-lg border border-signal-foul/40 bg-signal-foul/10 px-4 py-3 text-sm text-signal-foul">
                    <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
                    <span>{formError}</span>
                  </div>
                )}

                <form ref={formRef} onSubmit={handleSubmit} className="mt-6 space-y-4">
                  <div>
                    <label htmlFor="email" className="field-label">
                      Email
                    </label>
                    <input
                      id="email"
                      type="email"
                      autoComplete="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="you@example.com"
                      className="input-base"
                    />
                  </div>

                  {mode !== "magic" && (
                    <div>
                      <label htmlFor="password" className="field-label">
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
                        className="input-base"
                      />
                    </div>
                  )}

                  {mode === "register" && (
                    <div>
                      <label htmlFor="password2" className="field-label">
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
                        className="input-base"
                      />
                    </div>
                  )}

                  {/* hidden submit keeps Enter-to-submit working (ActionButton is type=button) */}
                  <input type="submit" hidden />
                  <div>
                    <ActionButton
                      task={submitTask}
                      onRun={() => formRef.current?.requestSubmit()}
                      label={
                        mode === "magic"
                          ? sendButtonLabel
                          : mode === "register"
                            ? "Create account"
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

                <div className="mt-3 flex flex-col items-start text-sm">
                  {mode !== "register" && (
                    <button type="button" onClick={() => switchMode("register")} className={quietLink}>
                      Create an account
                    </button>
                  )}
                  {mode !== "signin" && (
                    <button type="button" onClick={() => switchMode("signin")} className={quietLink}>
                      Sign in with a password
                    </button>
                  )}
                  {mode !== "magic" && (
                    <button type="button" onClick={() => switchMode("magic")} className={quietLink}>
                      {mode === "signin" ? "Forgot your password? Email me a sign-in link instead" : "Email me a sign-in link instead"}
                    </button>
                  )}
                </div>

                <p className="mt-5 text-sm text-white/60">
                  By signing in you agree to our{" "}
                  <Link href="/terms" className={quietLink}>Terms</Link>{" "}
                  and{" "}
                  <Link href="/privacy" className={quietLink}>Privacy Policy</Link>.
                </p>
              </>
            )}
          </div>

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
