"use client";

/**
 * MotoQuant Pro — Account Page
 * ==============================
 * Displays: email, tier, subscription status, license keys (copy + revoke),
 * saved-run garage, password management.
 * Requires authentication — redirects to /login if not signed in.
 *
 * Cockpit v3 (July 2026): shared `.card` surfaces + `.label-mono` voice,
 * SkeletonTable while the garage loads, branded inline confirms (no
 * alert()/confirm() anywhere), and ActionButton + useAsyncTask on every
 * submit so the button itself is the progress bar.
 * Subscription / license-key API calls unchanged.
 */

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Copy, Check } from "lucide-react";
import { useAuth } from "../../components/AuthProvider";
import TierBadge from "../../components/TierBadge";
import SiteNav from "../../components/SiteNav";
import SiteFooter from "../../components/SiteFooter";
import CodeComment from "../../components/CodeComment";
import { Reveal } from "../../components/Reveal";
import ActionButton from "../../components/ActionButton";
import { SkeletonCard, SkeletonTable } from "../../components/Skeleton";
import useAsyncTask from "../../lib/useAsyncTask";

import { API_URL_DIRECT as API_BASE } from "../../lib/api";

/**
 * DangerConfirm — the branded inline confirm pattern (replaces confirm()).
 * Renders a small red-tinted row: prompt + [danger action] [Keep — ghost].
 * While the task runs, the danger button becomes the ActionButton
 * running-state (progress strip in the button).
 */
function DangerConfirm({
  prompt,
  actionLabel,
  runningLabel,
  dismissLabel = "Keep",
  task,
  onConfirm,
  onDismiss,
}) {
  return (
    <div className="rounded-xl border border-brand-red/30 bg-brand-red/5 p-4">
      <p className="text-sm text-white/75">{prompt}</p>
      {task.error && (
        <p className="mt-2 text-sm text-brand-red/90">{task.error}</p>
      )}
      <div className="mt-3 flex flex-wrap items-center gap-2">
        {task.active ? (
          <ActionButton
            task={task}
            label={actionLabel}
            runningLabel={runningLabel}
            stoppable={false}
            className="btn-sm"
          />
        ) : (
          <button type="button" className="btn-danger btn-sm" onClick={onConfirm}>
            {actionLabel}
          </button>
        )}
        <button
          type="button"
          className="btn-ghost btn-sm"
          onClick={onDismiss}
          disabled={task.active}
        >
          {dismissLabel}
        </button>
      </div>
    </div>
  );
}

export default function AccountPage() {
  const router = useRouter();
  const { user, accessToken, isLoading, isAuthenticated, logout, refetchUser } = useAuth();

  const [keys, setKeys] = useState([]);
  const [keyMsg, setKeyMsg] = useState("");
  const [newKey, setNewKey] = useState("");
  const [copied, setCopied] = useState(false);
  const [revokeTarget, setRevokeTarget] = useState(null); // key id awaiting confirm
  const [cancelOpen, setCancelOpen] = useState(false); // sub-cancel confirm open
  const [subMsg, setSubMsg] = useState("");
  const [pwCurrent, setPwCurrent] = useState("");
  const [pwNew, setPwNew] = useState("");
  const [pwMsg, setPwMsg] = useState(null); // { tone: 'ok', text } — errors live on pwTask.error
  const [runs, setRuns] = useState([]);
  const [runsLoading, setRunsLoading] = useState(false);
  const [checkoutBanner, setCheckoutBanner] = useState(false);
  const pwFormRef = useRef(null);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.replace("/login");
  }, [isLoading, isAuthenticated, router]);

  useEffect(() => {
    if (user) setKeys(user.license_keys ?? []);
  }, [user]);

  // My Garage — saved runs for this account
  useEffect(() => {
    if (!accessToken) return;
    let cancelled = false;
    (async () => {
      setRunsLoading(true);
      try {
        const res = await fetch(`${API_BASE}/api/me/runs?limit=25`, {
          headers: { Authorization: `Bearer ${accessToken}` },
        });
        if (res.ok) {
          const data = await res.json();
          if (!cancelled) setRuns(data.runs || []);
        }
      } catch (e) {
        /* garage is best-effort */
      } finally {
        if (!cancelled) setRunsLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [accessToken]);

  // Post-checkout landing (?checkout=success) — window.location avoids a
  // useSearchParams/Suspense prerender dependency on this page.
  useEffect(() => {
    if (typeof window === "undefined") return;
    const qp = new URLSearchParams(window.location.search);
    if (qp.get("checkout") === "success") {
      setCheckoutBanner(true);
      refetchUser();
      window.history.replaceState({}, "", "/account");
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ── async tasks (one per submit — the button is the progress bar) ──────

  const genTask = useAsyncTask(async (signal) => {
    setKeyMsg("");
    setNewKey("");
    setCopied(false);
    const res = await fetch(`${API_BASE}/api/subscriptions/license-key`, {
      method: "POST",
      headers: { Authorization: `Bearer ${accessToken}` },
      signal,
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to generate key.");
    setNewKey(data.key);
    setKeyMsg(data.message);
    refetchUser();
    return data;
  });

  const revokeTask = useAsyncTask(async (signal, onProgress, keyId) => {
    const res = await fetch(`${API_BASE}/api/subscriptions/license-key/revoke`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ key_id: keyId }),
      signal,
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Revoke failed.");
    refetchUser();
    return data;
  });

  const cancelTask = useAsyncTask(async (signal) => {
    setSubMsg("");
    const res = await fetch(`${API_BASE}/api/subscriptions/cancel`, {
      method: "POST",
      headers: { Authorization: `Bearer ${accessToken}` },
      signal,
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Cancellation failed.");
    setSubMsg(data.message || "Subscription cancellation scheduled.");
    refetchUser();
    return data;
  });

  const pwTask = useAsyncTask(async (signal) => {
    setPwMsg(null);
    if (pwNew.length < 8) {
      throw new Error("New password must be at least 8 characters.");
    }
    const res = await fetch(`${API_BASE}/api/auth/password/change`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        current_password: user?.has_password ? pwCurrent : null,
        new_password: pwNew,
      }),
      signal,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(
        typeof data.detail === "string" ? data.detail : "Could not update password."
      );
    }
    setPwMsg({ tone: "ok", text: "Password updated." });
    setPwCurrent("");
    setPwNew("");
    refetchUser();
    return true;
  });

  if (isLoading || !user) {
    return (
      <div className="min-h-screen bg-black text-white">
        <SiteNav />
        <main className="pt-32 pb-20 px-4 sm:px-6">
          <div
            className="mx-auto max-w-3xl space-y-6"
            aria-busy="true"
            aria-label="Loading account"
          >
            <SkeletonCard rows={2} />
            <SkeletonCard rows={3} />
            <SkeletonCard rows={4} />
          </div>
        </main>
      </div>
    );
  }

  async function confirmRevoke(keyId) {
    const res = await revokeTask.run(keyId);
    if (res !== undefined) setRevokeTarget(null);
  }

  async function confirmCancelSub() {
    const res = await cancelTask.run();
    if (res !== undefined) setCancelOpen(false);
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
          {checkoutBanner && (
            <div className="rounded-xl bg-brand-green/10 border border-brand-green/40 px-5 py-4 text-sm text-brand-green/90">
              Payment received — thank you! Your plan activates within a minute
              (your tier refreshes automatically).
            </div>
          )}
          <div className="relative card p-6 sm:p-8 flex items-center justify-between">
            <div
              aria-hidden="true"
              className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-brand-orange/70 to-transparent"
            />
            <div>
              <div className="label-mono text-brand-orange mb-1">Account</div>
              <h1 className="font-display font-bold text-3xl sm:text-4xl text-white tracking-tight">
                {user.email.split("@")[0]}
              </h1>
            </div>
            <button
              onClick={logout}
              className="text-sm font-mono text-white/55 hover:text-brand-red transition-colors"
            >
              Sign out
            </button>
          </div>

          <Reveal y={18}>
          <section className="card p-6 sm:p-8">
            <h2 className="sr-only">Subscription</h2>
            <CodeComment className="mb-4">subscription · tier status</CodeComment>
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
                <a href="/pricing" className="btn-primary btn-sm mt-3">
                  See plans →
                </a>
              </div>
            )}

            {user.tier !== "free" && (
              <div className="mt-4 space-y-3">
                {subMsg && (
                  <p className="text-sm text-brand-amber">{subMsg}</p>
                )}
                {cancelOpen ? (
                  <DangerConfirm
                    prompt="Cancel your subscription? You keep access until the end of the billing period."
                    actionLabel="Cancel subscription"
                    runningLabel="Cancelling"
                    dismissLabel="Keep my plan"
                    task={cancelTask}
                    onConfirm={confirmCancelSub}
                    onDismiss={() => setCancelOpen(false)}
                  />
                ) : (
                  <button
                    onClick={() => { setCancelOpen(true); cancelTask.reset(); }}
                    className="text-sm text-white/45 hover:text-brand-red transition-colors underline"
                  >
                    Cancel subscription
                  </button>
                )}
              </div>
            )}
          </section>
          </Reveal>

          <Reveal y={18}>
          <section className="card p-6 sm:p-8">
            <div className="flex items-center justify-between mb-5">
              <h2 className="sr-only">Desktop license keys</h2>
              <CodeComment>license keys · desktop seats</CodeComment>
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
                  <div className="mb-5 rounded-xl bg-brand-green/10 border border-brand-green/40 p-4">
                    <p className="text-xs text-brand-green font-semibold mb-2">
                      {keyMsg} Copy it now — you won&rsquo;t see it again.
                    </p>
                    <div className="flex items-center gap-2">
                      <code className="flex-1 rounded bg-ink-0/60 px-3 py-2 text-xs text-brand-green/90 font-mono break-all">
                        {newKey}
                      </code>
                      <button
                        onClick={copyKey}
                        className="rounded bg-brand-green/15 hover:bg-brand-green/25 border border-brand-green/40 px-3 py-2 text-xs font-mono text-brand-green inline-flex items-center gap-1.5 transition-colors"
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
                        className="rounded-xl bg-ink-1 border border-white/10 px-4 py-3"
                      >
                        <div className="flex items-center justify-between gap-3">
                          <div className="text-sm text-white/80">
                            <span className="font-mono text-xs text-white/40">#{k.id}</span>
                            <span className="mx-2 text-white/20">·</span>
                            {k.device_id ? (
                              <span>Activated · last seen {k.last_seen_at ? new Date(k.last_seen_at).toLocaleDateString() : "never"}</span>
                            ) : (
                              <span className="text-brand-amber">Not yet activated</span>
                            )}
                          </div>
                          {revokeTarget !== k.id && (
                            <button
                              onClick={() => { setRevokeTarget(k.id); revokeTask.reset(); }}
                              className="text-xs text-brand-red/80 hover:text-brand-red underline"
                            >
                              Revoke
                            </button>
                          )}
                        </div>
                        {revokeTarget === k.id && (
                          <div className="mt-3">
                            <DangerConfirm
                              prompt="Revoke this key? The desktop seat frees up immediately and the key stops validating."
                              actionLabel="Revoke"
                              runningLabel="Revoking"
                              dismissLabel="Keep"
                              task={revokeTask}
                              onConfirm={() => confirmRevoke(k.id)}
                              onDismiss={() => setRevokeTarget(null)}
                            />
                          </div>
                        )}
                      </li>
                    ))}
                  </ul>
                )}

                {activeKeys.length < maxKeys && (
                  <div className="space-y-2">
                    {genTask.error && (
                      <p className="text-sm text-brand-red/90">{genTask.error}</p>
                    )}
                    <ActionButton
                      task={genTask}
                      onRun={() => genTask.run()}
                      label="+ Generate new license key"
                      runningLabel="Generating key"
                      stoppable={false}
                    />
                  </div>
                )}
              </>
            )}
          </section>
          </Reveal>

          <Reveal y={18}>
          <section className="card p-6 sm:p-8">
            <div className="flex items-center justify-between mb-5">
              <h2 className="sr-only">My garage — saved runs</h2>
              <CodeComment>garage · saved runs</CodeComment>
              <a href="/simulator" className="text-xs font-mono text-brand-orange hover:text-brand-orangeLight transition-colors">
                + New sim →
              </a>
            </div>
            {runsLoading && (
              <SkeletonTable rows={4} cols={4} aria-label="Loading your saved runs" />
            )}
            {!runsLoading && runs.length === 0 && (
              <p className="text-sm text-white/55">
                No saved runs yet. Run a simulation and hit{" "}
                <strong className="text-white">Save this run</strong> while signed
                in — it lands here.
              </p>
            )}
            {!runsLoading && runs.length > 0 && (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left label-mono border-b border-white/10">
                      <th className="py-2 pr-4">Bike</th>
                      <th className="py-2 pr-4 text-right">¼-mile</th>
                      <th className="py-2 pr-4 text-right">Trap</th>
                      <th className="py-2 pr-4 hidden sm:table-cell">Venue</th>
                      <th className="py-2 hidden sm:table-cell">Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {runs.map((r) => (
                      <tr key={r.id} className="border-b border-white/5">
                        <td className="py-2.5 pr-4 text-white/85">
                          {r.manufacturer ? `${r.manufacturer} ${r.model}` : `Run #${r.id}`}
                        </td>
                        <td className="py-2.5 pr-4 text-right font-mono tabular-nums text-brand-orange">
                          {r.et_quarter_s != null ? `${r.et_quarter_s.toFixed(3)}s` : "—"}
                        </td>
                        <td className="py-2.5 pr-4 text-right font-mono tabular-nums text-white/70">
                          {r.trap_speed_kmh != null ? `${r.trap_speed_kmh.toFixed(1)} km/h` : "—"}
                        </td>
                        <td className="py-2.5 pr-4 text-white/55 hidden sm:table-cell">{r.venue || "—"}</td>
                        <td className="py-2.5 text-white/45 hidden sm:table-cell">
                          {r.created_at ? new Date(r.created_at).toLocaleDateString() : "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
          </Reveal>

          <Reveal y={18}>
          <section className="card p-6 sm:p-8">
            <h2 className="sr-only">Security</h2>
            <CodeComment className="mb-4">security · password</CodeComment>
            {!user.has_password && (
              <p className="mb-4 text-sm text-white/55">
                You currently sign in via magic link. Add a password to sign in
                directly — the magic-link option stays available either way.
              </p>
            )}
            {pwMsg && (
              <p className="mb-3 text-sm text-brand-green">{pwMsg.text}</p>
            )}
            {pwTask.error && (
              <p className="mb-3 text-sm text-brand-red/90">{pwTask.error}</p>
            )}
            <form
              ref={pwFormRef}
              onSubmit={(e) => {
                e.preventDefault();
                if (!pwTask.active) pwTask.run();
              }}
              className="space-y-3 max-w-sm"
            >
              {user.has_password && (
                <input
                  type="password"
                  autoComplete="current-password"
                  required
                  value={pwCurrent}
                  onChange={(e) => setPwCurrent(e.target.value)}
                  placeholder="Current password"
                  className="input-base font-mono"
                />
              )}
              <input
                type="password"
                autoComplete="new-password"
                required
                minLength={8}
                value={pwNew}
                onChange={(e) => setPwNew(e.target.value)}
                placeholder="New password (8+ characters)"
                className="input-base font-mono"
              />
              {/* hidden submit keeps Enter-to-submit working (ActionButton is type=button) */}
              <input type="submit" hidden />
              <ActionButton
                task={pwTask}
                onRun={() => pwFormRef.current?.requestSubmit()}
                label={user.has_password ? "Change password" : "Set a password"}
                runningLabel="Saving"
                stoppable={false}
              />
            </form>
          </section>
          </Reveal>
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
