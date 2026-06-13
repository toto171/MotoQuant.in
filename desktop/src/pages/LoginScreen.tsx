// Login gate. Shown to any unauthenticated user — the simulator is never
// rendered until the hosted server has issued a valid session. Supports
// password sign-in, registration, and magic-link (email) flows, matching the
// hosted /api/auth/* contract.

import { useState } from "react";
import { Gauge, Loader2 } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { api, ApiRequestError } from "@/lib/api";

type Mode = "login" | "register" | "magic";

export function LoginScreen() {
  const { loginPassword, registerPassword, verifyMagicLink } = useAuth();
  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [magicToken, setMagicToken] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setNotice(null);
    setBusy(true);
    try {
      if (mode === "login") {
        await loginPassword(email.trim(), password);
      } else if (mode === "register") {
        await registerPassword(email.trim(), password);
      } else {
        // magic-link: either request a link, or verify a pasted token.
        if (magicToken.trim()) {
          await verifyMagicLink(magicToken.trim());
        } else {
          const res = await api.authMagicLink(email.trim());
          setNotice(
            res.message ||
              "Check your email for a sign-in link, then paste the token below.",
          );
        }
      }
    } catch (err) {
      if (err instanceof ApiRequestError) {
        setError(
          err.status === 0
            ? "Can't reach MotoQuant servers. Check your connection and try again."
            : err.detail,
        );
      } else {
        setError(err instanceof Error ? err.message : "Sign-in failed.");
      }
    } finally {
      setBusy(false);
    }
  };

  const tab = (m: Mode, label: string) => (
    <button
      type="button"
      onClick={() => {
        setMode(m);
        setError(null);
        setNotice(null);
      }}
      className={
        "px-3 py-1.5 text-sm rounded-md transition-colors focus-visible:outline-2 focus-visible:outline-signal-500 " +
        (mode === m
          ? "bg-signal-500 text-carbon-950 font-medium"
          : "text-carbon-400 hover:text-carbon-100")
      }
      aria-pressed={mode === m}
    >
      {label}
    </button>
  );

  return (
    <div className="min-h-screen flex items-center justify-center bg-carbon-950 px-4">
      <div className="w-full max-w-sm">
        <div className="flex items-center gap-2 justify-center mb-6">
          <Gauge className="w-6 h-6 text-signal-500" aria-hidden="true" />
          <span className="text-lg font-semibold tracking-tight">MotoQuant Pro</span>
        </div>

        <div className="card p-6 space-y-5">
          <div>
            <h1 className="text-base font-semibold text-carbon-100">
              Sign in to continue
            </h1>
            <p className="text-xs text-carbon-500 mt-1 leading-relaxed">
              MotoQuant Pro runs against the hosted simulation engine. An active
              account is required.
            </p>
          </div>

          <div className="flex gap-1 rounded-lg bg-carbon-800 p-1" role="tablist">
            {tab("login", "Sign in")}
            {tab("register", "Register")}
            {tab("magic", "Magic link")}
          </div>

          <form onSubmit={submit} className="space-y-3">
            <label className="block">
              <span className="label text-[10px] text-carbon-500">Email</span>
              <input
                type="email"
                required
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input text-sm mt-1"
                placeholder="you@example.com"
              />
            </label>

            {(mode === "login" || mode === "register") && (
              <label className="block">
                <span className="label text-[10px] text-carbon-500">Password</span>
                <input
                  type="password"
                  required
                  autoComplete={mode === "login" ? "current-password" : "new-password"}
                  minLength={mode === "register" ? 8 : 1}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input text-sm mt-1"
                  placeholder="••••••••"
                />
              </label>
            )}

            {mode === "magic" && (
              <label className="block">
                <span className="label text-[10px] text-carbon-500">
                  Sign-in token (paste from email)
                </span>
                <input
                  type="text"
                  value={magicToken}
                  onChange={(e) => setMagicToken(e.target.value)}
                  className="input text-sm mt-1 font-mono"
                  placeholder="optional — leave blank to request a link"
                />
              </label>
            )}

            {error && (
              <div
                className="text-xs text-stop-400 bg-stop-500/5 border border-stop-500/30 rounded px-3 py-2"
                role="alert"
              >
                {error}
              </div>
            )}
            {notice && (
              <div className="text-xs text-go-400 bg-go-500/5 border border-go-500/30 rounded px-3 py-2">
                {notice}
              </div>
            )}

            <button
              type="submit"
              disabled={busy}
              className="btn-primary w-full justify-center disabled:opacity-60"
            >
              {busy && <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />}
              {mode === "login"
                ? "Sign in"
                : mode === "register"
                  ? "Create account"
                  : magicToken.trim()
                    ? "Verify token"
                    : "Email me a link"}
            </button>
          </form>

          <p className="text-[11px] text-carbon-600 leading-relaxed text-center">
            Don't have a license? Plans &amp; pricing at{" "}
            <span className="font-mono text-carbon-400">motoquant.in/pricing</span>
          </p>
        </div>
      </div>
    </div>
  );
}
