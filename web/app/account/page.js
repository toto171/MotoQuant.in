"use client";

/**
 * MotoQuant Pro — Account Page
 * ==============================
 * Displays: email, tier, subscription status, license keys (copy + revoke).
 * Requires authentication — redirects to /login if not signed in.
 */

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../../components/AuthProvider";
import TierBadge from "../../components/TierBadge";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "https://web-production-de6eb.up.railway.app";

export default function AccountPage() {
  const router = useRouter();
  const { user, accessToken, isLoading, isAuthenticated, logout, refetchUser } = useAuth();

  const [keys, setKeys] = useState([]);
  const [generatingKey, setGeneratingKey] = useState(false);
  const [keyMsg, setKeyMsg] = useState("");
  const [newKey, setNewKey] = useState("");
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
      <main className="flex min-h-screen items-center justify-center bg-gray-950">
        <p className="text-gray-500 text-sm">Loading account…</p>
      </main>
    );
  }

  // ── Actions ────────────────────────────────────────────────────────────────

  async function generateKey() {
    setGeneratingKey(true);
    setKeyMsg("");
    setNewKey("");
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

  const canGenerateKey = user.tier !== "free";
  const maxKeys = { free: 0, pro: 1, studio: 5 }[user.tier] ?? 0;
  const activeKeys = keys.filter((k) => !k.revoked);

  return (
    <main className="min-h-screen bg-gray-950 py-12 px-4">
      <div className="mx-auto max-w-2xl space-y-8">

        {/* Header */}
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-white">Account</h1>
          <button
            onClick={logout}
            className="text-sm text-gray-400 hover:text-red-400 transition-colors"
          >
            Sign out
          </button>
        </div>

        {/* Profile card */}
        <section className="rounded-2xl bg-gray-900 border border-gray-800 p-6">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500 mb-4">
            Profile
          </h2>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-white font-medium">{user.email}</p>
              <p className="mt-0.5 text-sm text-gray-400">
                {user.subscription_status
                  ? `Subscription: ${user.subscription_status}`
                  : "No active subscription"}
              </p>
            </div>
            <TierBadge tier={user.tier} size="md" />
          </div>

          {user.tier === "free" && (
            <div className="mt-4 rounded-xl bg-orange-900/20 border border-orange-800/50 p-4">
              <p className="text-sm text-orange-300">
                Upgrade to <strong>Pro</strong> for unlimited sims, full analysis suite, and leaderboard saves.
              </p>
              <a
                href="/pricing"
                className="mt-3 inline-flex items-center gap-1 rounded-lg bg-orange-500 px-4 py-2
                           text-sm font-semibold text-white hover:bg-orange-600 transition-colors"
              >
                See plans →
              </a>
            </div>
          )}

          {user.tier !== "free" && (
            <div className="mt-4">
              {subMsg && (
                <p className="mb-2 text-sm text-yellow-400">{subMsg}</p>
              )}
              <button
                onClick={cancelSubscription}
                disabled={cancelling}
                className="text-sm text-gray-500 hover:text-red-400 underline transition-colors
                           disabled:opacity-50"
              >
                {cancelling ? "Cancelling…" : "Cancel subscription"}
              </button>
            </div>
          )}
        </section>

        {/* Desktop license keys */}
        <section className="rounded-2xl bg-gray-900 border border-gray-800 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500">
              Desktop License Keys
            </h2>
            <span className="text-xs text-gray-500">
              {activeKeys.length} / {maxKeys} used
            </span>
          </div>

          {!canGenerateKey && (
            <p className="text-sm text-gray-500">
              License keys are available on Pro and Studio plans.{" "}
              <a href="/pricing" className="text-orange-400 underline">Upgrade →</a>
            </p>
          )}

          {canGenerateKey && (
            <>
              {newKey && (
                <div className="mb-4 rounded-lg bg-green-900/30 border border-green-700 p-4">
                  <p className="text-xs text-green-400 font-semibold mb-1">
                    {keyMsg} Copy it now — you won't see it again.
                  </p>
                  <div className="flex items-center gap-2">
                    <code className="flex-1 rounded bg-gray-800 px-3 py-1.5 text-xs text-green-300 font-mono break-all">
                      {newKey}
                    </code>
                    <button
                      onClick={() => navigator.clipboard.writeText(newKey)}
                      className="rounded bg-green-700 px-3 py-1.5 text-xs text-white hover:bg-green-600"
                    >
                      Copy
                    </button>
                  </div>
                </div>
              )}

              {/* Existing keys */}
              {activeKeys.length > 0 && (
                <ul className="mb-4 space-y-2">
                  {activeKeys.map((k) => (
                    <li
                      key={k.id}
                      className="flex items-center justify-between rounded-lg bg-gray-800 px-4 py-2"
                    >
                      <div className="text-sm text-gray-300">
                        <span className="font-mono text-xs text-gray-500">#{k.id}</span>
                        {" · "}
                        {k.device_id ? (
                          <span>Activated · last seen {k.last_seen_at ? new Date(k.last_seen_at).toLocaleDateString() : "never"}</span>
                        ) : (
                          <span className="text-yellow-400">Not yet activated</span>
                        )}
                      </div>
                      <button
                        onClick={() => revokeKey(k.id)}
                        disabled={revoking === k.id}
                        className="text-xs text-red-400 hover:text-red-300 underline disabled:opacity-50"
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
                  className="rounded-lg bg-gray-700 px-4 py-2 text-sm font-medium text-white
                             hover:bg-gray-600 disabled:opacity-50 transition-colors"
                >
                  {generatingKey ? "Generating…" : "+ Generate new license key"}
                </button>
              )}
            </>
          )}
        </section>

        {/* Footer links */}
        <div className="flex gap-4 text-xs text-gray-600">
          <a href="/terms" className="hover:text-gray-400">Terms of Service</a>
          <a href="/privacy" className="hover:text-gray-400">Privacy Policy</a>
          <a href="mailto:hello@motoquant.in" className="hover:text-gray-400">Support</a>
        </div>
      </div>
    </main>
  );
}
