"use client";

/**
 * MotoQuant Pro — Account Page
 * ==============================
 * Displays: email, tier, subscription status, license keys (copy + revoke).
 * Requires authentication — redirects to /login if not signed in.
 *
 * Direction A refit (April 2026): SiteNav + black canvas + brand-orange
 * accents. Subscription / license-key API calls unchanged.
 */

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Copy, Check } from "lucide-react";
import { useAuth } from "../../components/AuthProvider";
import TierBadge from "../../components/TierBadge";
import SiteNav from "../../components/SiteNav";
import SiteFooter from "../../components/SiteFooter";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "https://motoquant-api.onrender.com";

export default function AccountPage() {
  const router = useRouter();
  const { user, accessToken, isLoading, isAuthenticated, logout, refetchUser } = useAuth();

  const [keys, setKeys] = useState([]);
  const [generatingKey, setGeneratingKey] = useState(false);
  const [keyMsg, setKeyMsg] = useState("");
  const [newKey, setNewKey] = useState("");
  const [copied, setCopied] = useState(false);
  const [revoking, setRevoking] = useState(null);
  const [cancelling, setCancelling] = useState(false);
  const [subMsg, setSubMsg] = useState("");

  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.replace("/login");
  }, [isLoading, isAuthenticated, router]);

  useEffect(() => {
    if (user) setKeys(user.license_keys ?? []);
  }, [user]);

  if (isLoading || !user) {
    return (
      <div className="min-h-screen bg-black text-white">
        <SiteNav />
        <main className="flex min-h-[calc(100vh-4rem)] items-center justify-center">
          <p className="text-white/55 text-sm font-mono">Loading account…</p>
        </main>
      </div>
    );
  }

  async function generateKey() {
    setGeneratingKey(true);
    setKeyMsg("");
    setNewKey("");
    setCopied(false);
    try {
      const res = await fetch(`${API_BASE}/api/subscriptions/license-key`, {
        method: "POST",
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to generate key.");
      setNewKey(data.key);
      setKeyMsg(data.message);
      refetchUser();
    } catch (err) {
      setKeyMsg(err.message);
    } finally {
      setGeneratingKey(false);
    }
  }

  async function revokeKey(keyId) {
    setRevoking(keyId);
    try {
      const res = await fetch(`${API_BASE}/api/subscriptions/license-key/revoke`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${accessToken}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ key_id: keyId }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Revoke failed.");
      refetchUser();
    } catch (err) {
      alert(err.message);
    } finally {
      setRevoking(null);
    }
  }

  async function cancelSubscription() {
    if (!confirm("Cancel your subscription? You keep access until the end of the billing period.")) return;
    setCancelling(true);
    setSubMsg("");
    try {
      const res = await fetch(`${API_BASE}/api/subscriptions/cancel`, {
        method: "POST",
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Cancellation failed.");
      setSubMsg(data.message || "Subscription cancellation scheduled.");
      refetchUser();
    } catch (err) {
      setSubMsg(err.message);
    } finally {
      setCancelling(false);
    }
  }

  async function copyKey() {
    try {
      await navigator.clipboard.writeText(newKey);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch (e) {}
  }

  const canGenerateKey = user.tier !== "free";
  const maxKeys = { free: 0, pro: 1, studio: 5 }[user.tier] ?? 0;
  const activeKeys = keys.filter((k) => !k.revoked);

  return (
    <div className="min-h-screen bg-black text-white">
      <SiteNav />
      <main className="pt-32 pb-20 px-4 sm:px-6">
        <div className="mx-auto max-w-3xl space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-[10px] font-mono uppercase tracking-[0.25em] text-brand-orange mb-1">
                Account
              </div>
              <h1 className="font-display font-bold text-3xl sm:text-4xl text-white tracking-tight">
                {user.email.split("@")[0]}
              </h1>
            </div>
            <button
              onClick={logout}
              className="text-sm font-mono text-white/55 hover:text-red-300 transition-colors"
            >
              Sign out
            </button>
          </div>

          <section className="rounded-2xl bg-ink-1/60 border border-white/10 p-6 sm:p-8">
            <div className="text-[10px] font-mono uppercase tracking-[0.25em] text-white/45 mb-4">
              Profile
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-white font-medium">{user.email}</p>
                <p className="mt-1 text-sm text-white/55">
                  {user.subscription_status
                    ? `Subscription: ${user.subscription_status}`
                    : "No active subscription"}
                </p>
              </div>
              <TierBadge tier={user.tier} size="md" />
            </div>

            {user.tier === "free" && (
              <div className="mt-5 rounded-xl bg-brand-orange/10 border border-brand-orange/30 p-4">
                <p className="text-sm text-brand-orangeLight">
                  Upgrade to <strong className="text-white">Pro</strong> for unlimited sims, full analysis suite, and leaderboard saves.
                </p>
                <a
                  href="/pricing"
                  className="mt-3 inline-flex items-center gap-1 rounded-md bg-brand-orange px-4 py-2 text-sm font-display font-bold text-black hover:bg-brand-orangeLight transition-colors"
                >
                  See plans →
                </a>
              </div>
            )}

            {user.tier !== "free" && (
              <div className="mt-4">
                {subMsg && (
                  <p className="mb-2 text-sm text-amber-300">{subMsg}</p>
                )}
                <button
                  onClick={cancelSubscription}
                  disabled={cancelling}
                  className="text-sm text-white/45 hover:text-red-300 transition-colors disabled:opacity-50 underline"
                >
                  {cancelling ? "Cancelling…" : "Cancel subscription"}
                </button>
              </div>
            )}
          </section>

          <section className="rounded-2xl bg-ink-1/60 border border-white/10 p-6 sm:p-8">
            <div className="flex items-center justify-between mb-5">
              <div className="text-[10px] font-mono uppercase tracking-[0.25em] text-white/45">
                Desktop License Keys
              </div>
              <span className="text-xs font-mono text-white/45">
                {activeKeys.length} / {maxKeys} used
              </span>
            </div>

            {!canGenerateKey && (
              <p className="text-sm text-white/55">
                License keys are available on Pro and Studio plans.{" "}
                <a href="/pricing" className="text-brand-orange hover:text-brand-orangeLight">Upgrade →</a>
              </p>
            )}

            {canGenerateKey && (
              <>
                {newKey && (
                  <div className="mb-5 rounded-xl bg-emerald-900/25 border border-emerald-500/40 p-4">
                    <p className="text-xs text-emerald-300 font-semibold mb-2">
                      {keyMsg} Copy it now — you won&rsquo;t see it again.
                    </p>
                    <div className="flex items-center gap-2">
                      <code className="flex-1 rounded bg-black/60 px-3 py-2 text-xs text-emerald-200 font-mono break-all">
                        {newKey}
                      </code>
                      <button
                        onClick={copyKey}
                        className="rounded bg-emerald-700 hover:bg-emerald-600 px-3 py-2 text-xs font-mono text-white inline-flex items-center gap-1.5 transition-colors"
                      >
                        {copied ? <Check size={12} /> : <Copy size={12} />}
                        {copied ? "Copied" : "Copy"}
                      </button>
                    </div>
                  </div>
                )}

                {activeKeys.length > 0 && (
                  <ul className="mb-5 space-y-2">
                    {activeKeys.map((k) => (
                      <li
                        key={k.id}
                        className="flex items-center justify-between rounded-md bg-black/40 border border-white/5 px-4 py-3"
                      >
                        <div className="text-sm text-white/80">
                          <span className="font-mono text-xs text-white/40">#{k.id}</span>
                          <span className="mx-2 text-white/20">·</span>
                          {k.device_id ? (
                            <span>Activated · last seen {k.last_seen_at ? new Date(k.last_seen_at).toLocaleDateString() : "never"}</span>
                          ) : (
                            <span className="text-amber-300">Not yet activated</span>
                          )}
                        </div>
                        <button
                          onClick={() => revokeKey(k.id)}
                          disabled={revoking === k.id}
                          className="text-xs text-red-300 hover:text-red-200 underline disabled:opacity-50"
                        >
                          {revoking === k.id ? "Revoking…" : "Revoke"}
                        </button>
                      </li>
                    ))}
                  </ul>
                )}

                {activeKeys.length < maxKeys && (
                  <button
                    onClick={generateKey}
                    disabled={generatingKey}
                    className="rounded-md bg-white/10 hover:bg-white/15 border border-white/15 px-4 py-2.5 text-sm font-display font-bold text-white disabled:opacity-50 transition-colors"
                  >
                    {generatingKey ? "Generating…" : "+ Generate new license key"}
                  </button>
                )}
              </>
            )}
          </section>
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
