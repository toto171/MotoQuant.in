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
 * Cockpit v3 (July 2026): the submit is an ActionButton + useAsyncTask
 * (staged progress, cold-start caption for free), the ?token= verification
 * shows a staged SimProgress bar, inputs are `.input-base`, labels
 * `.label-mono`. Auth flows + EXP-007 unchanged.
 */

import { Suspense, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Mail, KeyRound, AlertCircle } from "lucide-react";
import { useAuth } from "../../components/AuthProvider";
import SiteNav from "../../components/SiteNav";
import SiteFooter from "../../components/SiteFooter";
import CodeComment from "../../components/CodeComment";
import SimProgress from "../../components/SimProgress";
import ActionButton from "../../components/ActionButton";
import { SkeletonCard } from "../../components/Skeleton";
import useAsyncTask from "../../lib/useAsyncTask";

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
    signin: ["Sign in", "Welcome back — pick up where you left off."],
    register: ["Create your account", "Free during the open beta — every Pro feature unlocked."],
    magic: ["Magic-link sign-in", "No password needed — we’ll email you a sign-in link."],
  };
  const [heading, subheading] = headings[mode];
  const formError = (status === "error" ? errorMsg : "") || submitTask.error;

  const tabClass = (m) =>
    [
      "flex-1 px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] rounded-md transition-colors whitespace-nowrap",
      mode === m
        ? "bg-brand-orange/15 text-brand-orange border border-brand-orange/40"
        : "text-white/45 hover:text-white border border-transparent",
    ].join(" ");

  return (
    <div className="min-h-screen bg-black text-white">
      <SiteNav />
      <main id="main" className="flex min-h-[calc(100vh-4rem)] items-center justify-center px-4 pt-20 pb-12">
        <div className="relative w-full max-w-sm space-y-8">
          <div
            aria-hidden="true"
            className="pointer-events-none absolute -inset-x-24 -top-24 -bottom-16 bg-[radial-gradient(ellipse_at_center,rgba(255,94,31,0.10),transparent_65%)]"
          />
          <div className="relative text-center space-y-3">
            <CodeComment center>auth gate · jwt session</CodeComment>
            <p className="font-display font-bold text-2xl text-gradient-orange">
              The physics of faster
            </p>
          </div>

          <div className="relative card bg-ink-1/70 p-8 shadow-2xl">
            <div
              aria-hidden="true"
              className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-brand-orange/70 to-transparent"
            />
            {status === "verifying" && (
              <div className="text-center text-white/85 py-4">
                <KeyRound className="w-8 h-8 mx-auto text-brand-orange mb-4" />
                <p className="font-display font-bold text-lg mb-4">Verifying your sign-in link</p>
                <SimProgress
                  active
                  progress={null}
                  label="Verifying your sign-in link"
                  className="text-left"
                />
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
                  <div className="mt-5 rounded-lg bg-brand-amber/10 border border-brand-amber/30 p-3 text-left">
                    <p className="label-mono text-brand-amber font-bold">DEV TOKEN</p>
                    <p className="mt-1 text-xs text-brand-amber/80 break-all font-mono">{devToken}</p>
                    <button
                      onClick={() => verifyToken(devToken)}
                      className="mt-2 rounded bg-brand-amber px-3 py-1 text-xs font-semibold text-black hover:bg-brand-amber/85 transition-colors"
                    >
                      Auto-verify (dev only)
                    </button>
                  </div>
                )}
                <button
                  onClick={() => { setStatus("idle"); setDevToken(""); submitTask.reset(); }}
                  className="mt-6 text-sm text-brand-accent hover:text-white transition-colors"
                >
                  Try a different email
                </button>
              </div>
            )}

            {(status === "idle" || status === "error") && (
              <>
                <div className="flex gap-1.5 mb-6">
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

                <h2 className="font-display font-bold text-2xl text-white">{heading}</h2>
                <p className="mt-1 text-sm text-white/55">{subheading}</p>

                {formError && (
                  <div className="mt-5 rounded-lg bg-brand-red/10 border border-brand-red/40 px-4 py-3 text-sm text-brand-red/90 flex items-start gap-2">
                    <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                    <span>{formError}</span>
                  </div>
                )}

                <form ref={formRef} onSubmit={handleSubmit} className="mt-6 space-y-4">
                  <div>
                    <label htmlFor="email" className="block label-mono mb-2">
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
                      <label htmlFor="password" className="block label-mono mb-2">
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
                      <label htmlFor="password2" className="block label-mono mb-2">
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
                    className="mt-4 text-xs text-brand-accent hover:text-white transition-colors"
                  >
                    Forgot password? Sign in with a magic link instead →
                  </button>
                )}

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
            {mode === "register" ? (
              <>
                Already racing with us?{" "}
                <button onClick={() => switchMode("signin")} className="text-brand-orange hover:text-brand-orangeLight transition-colors">
                  Sign in →
                </button>
              </>
            ) : (
              <>
                New to MotoQuant?{" "}
                <button onClick={() => switchMode("register")} className="text-brand-orange hover:text-brand-orangeLight transition-colors">
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
        <div className="min-h-screen bg-black flex items-center justify-center px-4">
          <div className="w-full max-w-sm">
            <SkeletonCard rows={4} />
          </div>
        </div>
      }
    >
      <LoginPageInner />
    </Suspense>
  );
}
