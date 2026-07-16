"use client";

/**
 * MotoQuant Pro — Account Page
 * ==============================
 * Displays: email, tier, subscription status, license keys (copy + revoke),
 * saved-run garage, password management.
 * Requires authentication — redirects to /login if not signed in.
 *
 * IGNITION v5 (July 2026): PageHero ("Your garage") + stacked `.card`
 * sections — Profile/Tier, Garage (bike names in display face, ETs mono,
 * venue chips, rows link to /r/[id]), License keys as `.timeslip` rows with
 * `.btn-danger` revokes, Security, Danger zone. Branded inline confirms
 * (no alert()/confirm() anywhere) and ActionButton + useAsyncTask on every
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
import PageHero from "../../components/PageHero";
import { Reveal } from "../../components/Reveal";
import ActionButton from "../../components/ActionButton";
import { SkeletonCard, SkeletonTable } from "../../components/Skeleton";
import useAsyncTask from "../../lib/useAsyncTask";

import { API_URL_DIRECT as API_BASE } from "../../lib/api";

/**
 * DangerConfirm — the branded inline confirm pattern (replaces confirm()).
 * Renders a small foul-tinted row: prompt + [danger action] [Keep — ghost].
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
    <div className="rounded-xl border border-signal-foul/30 bg-signal-foul/5 p-4">
      <p className="text-sm text-white/75">{prompt}</p>
      {task.error && (
        <p className="mt-2 text-sm text-signal-foul">{task.error}</p>
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
      <div className="min-h-screen bg-asphalt-0 text-white">
        <SiteNav />
        <main id="main" className="pt-32 pb-20 px-4 sm:px-6">
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

  const sectionTitle =
    "font-display font-semibold text-lg md:text-xl text-white";

  return (
    <div className="min-h-screen bg-asphalt-0 text-white">
      <SiteNav />
      <PageHero
        align="center"
        kicker="account"
        title={<>Your <span className="text-accent">garage</span></>}
        sub="Saved runs, license seats and security for your MotoQuant account."
      />
      <main id="main" className="pb-20 px-4 sm:px-6">
        <div className="mx-auto max-w-3xl space-y-6">
          {checkoutBanner && (
            <div className="rounded-xl border border-signal-go/40 bg-signal-go/10 px-5 py-4 text-sm text-signal-go">
              Payment received — thank you! Your plan activates within a minute
              (your tier refreshes automatically).
            </div>
          )}

          {/* ── Profile / tier ─────────────────────────────────────────── */}
          <Reveal y={18}>
          <section className="card p-6 sm:p-8">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <h2 className={sectionTitle}>Profile</h2>
                <p className="mt-3 font-medium text-white">{user.email}</p>
                <p className="mt-1 text-sm text-white/55">
                  {user.subscription_status
                    ? `Subscription: ${user.subscription_status}`
                    : "No active subscription"}
                </p>
              </div>
              <div className="flex items-center gap-3">
                <TierBadge tier={user.tier} size="md" />
                <button onClick={logout} className="btn-ghost btn-sm">
                  Sign out
                </button>
              </div>
            </div>

            {user.tier === "free" && (
              <div className="mt-5 rounded-xl border border-accent/30 bg-accent/[0.06] p-4">
                <p className="text-sm text-white/75">
                  Upgrade to <strong className="text-white">Pro</strong> for unlimited sims, full analysis suite, and leaderboard saves.
                </p>
                <a href="/pricing" className="btn-primary btn-sm mt-3">
                  See plans →
                </a>
              </div>
            )}
          </section>
          </Reveal>

          {/* ── Garage — saved runs ────────────────────────────────────── */}
          <Reveal y={18}>
          <section className="card p-6 sm:p-8">
            <div className="mb-5 flex items-center justify-between">
              <h2 className={sectionTitle}>Garage</h2>
              <a
                href="/simulator"
                className="font-mono text-xs text-accent hover:text-accent-bright transition-colors"
              >
                + New sim →
              </a>
            </div>
            {runsLoading && (
              <SkeletonTable rows={4} cols={4} aria-label="Loading your saved runs" />
            )}
            {!runsLoading && runs.length === 0 && (
              <p className="text-sm text-white/65">
                No saved runs yet. Run a simulation and hit{" "}
                <strong className="text-white">Save this run</strong> while signed
                in — it lands here.
              </p>
            )}
            {!runsLoading && runs.length > 0 && (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-white/10 text-left label-mono">
                      <th className="py-2 pr-4 font-medium">Bike</th>
                      <th className="py-2 pr-4 text-right font-medium">¼-mile</th>
                      <th className="py-2 pr-4 text-right font-medium">Trap</th>
                      <th className="hidden py-2 pr-4 font-medium sm:table-cell">Venue</th>
                      <th className="hidden py-2 font-medium sm:table-cell">Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {runs.map((r) => (
                      <tr key={r.id} className="border-b border-white/5">
                        <td className="py-2.5 pr-4">
                          <a
                            href={`/r/${r.id}`}
                            className="font-display font-semibold text-white/90 hover:text-white transition-colors"
                          >
                            {r.manufacturer ? `${r.manufacturer} ${r.model}` : `Run #${r.id}`}
                          </a>
                        </td>
                        <td className="py-2.5 pr-4 text-right font-mono tabular-nums font-medium text-white">
                          {r.et_quarter_s != null ? `${r.et_quarter_s.toFixed(3)}s` : "—"}
                        </td>
                        <td className="py-2.5 pr-4 text-right font-mono tabular-nums text-white/70">
                          {r.trap_speed_kmh != null ? `${r.trap_speed_kmh.toFixed(1)} km/h` : "—"}
                        </td>
                        <td className="hidden py-2.5 pr-4 sm:table-cell">
                          {r.venue ? (
                            <span className="chip">{r.venue}</span>
                          ) : (
                            <span className="text-white/40">—</span>
                          )}
                        </td>
                        <td className="hidden py-2.5 font-mono text-xs text-white/45 sm:table-cell">
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

          {/* ── License keys — device seats ────────────────────────────── */}
          <Reveal y={18}>
          <section className="card p-6 sm:p-8">
            <div className="mb-5 flex items-center justify-between">
              <h2 className={sectionTitle}>License keys</h2>
              <span className="chip">
                {activeKeys.length} / {maxKeys} used
              </span>
            </div>

            {!canGenerateKey && (
              <p className="text-sm text-white/65">
                License keys are available on Pro and Studio plans.{" "}
                <a
                  href="/pricing"
                  className="text-white/80 underline decoration-white/25 underline-offset-2 hover:text-white transition-colors"
                >
                  Upgrade →
                </a>
              </p>
            )}

            {canGenerateKey && (
              <>
                {newKey && (
                  <div className="mb-5 rounded-xl border border-signal-go/40 bg-signal-go/10 p-4">
                    <p className="mb-2 text-xs font-semibold text-signal-go">
                      {keyMsg} Copy it now — you won&rsquo;t see it again.
                    </p>
                    <div className="flex items-center gap-2">
                      <code className="flex-1 break-all rounded bg-asphalt-0/60 px-3 py-2 font-mono text-xs text-signal-go/90">
                        {newKey}
                      </code>
                      <button
                        onClick={copyKey}
                        className="inline-flex items-center gap-1.5 rounded border border-signal-go/40 bg-signal-go/15 px-3 py-2 font-mono text-xs text-signal-go hover:bg-signal-go/25 transition-colors"
                      >
                        {copied ? <Check size={12} /> : <Copy size={12} />}
                        {copied ? "Copied" : "Copy"}
                      </button>
                    </div>
                  </div>
                )}

                {activeKeys.length > 0 && (
                  <div className="timeslip mb-5">
                    {activeKeys.map((k) => (
                      <div key={k.id}>
                        <div className="timeslip-row items-center">
                          <span className="text-white/80">
                            <span className="text-white/40">#{k.id}</span>
                            <span className="mx-2 text-white/20">·</span>
                            {k.device_id ? (
                              <span>
                                Activated · last seen{" "}
                                {k.last_seen_at
                                  ? new Date(k.last_seen_at).toLocaleDateString()
                                  : "never"}
                              </span>
                            ) : (
                              <span className="text-signal-stage">Not yet activated</span>
                            )}
                          </span>
                          {revokeTarget !== k.id && (
                            <button
                              onClick={() => { setRevokeTarget(k.id); revokeTask.reset(); }}
                              className="btn-danger btn-sm"
                            >
                              Revoke
                            </button>
                          )}
                        </div>
                        {revokeTarget === k.id && (
                          <div className="my-3">
                            <DangerConfirm
                              prompt="Revoke this key? The seat frees up immediately and the key stops validating."
                              actionLabel="Revoke"
                              runningLabel="Revoking"
                              dismissLabel="Keep"
                              task={revokeTask}
                              onConfirm={() => confirmRevoke(k.id)}
                              onDismiss={() => setRevokeTarget(null)}
                            />
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {activeKeys.length < maxKeys && (
                  <div className="space-y-2">
                    {genTask.error && (
                      <p className="text-sm text-signal-foul">{genTask.error}</p>
                    )}
                    <ActionButton
                      task={genTask}
                      onRun={() => genTask.run()}
                      label="+ Generate new license key"
                      runningLabel="Generating key"
                      stoppable={false}
                      variant="ghost"
                    />
                  </div>
                )}
              </>
            )}
          </section>
          </Reveal>

          {/* ── Security — password ────────────────────────────────────── */}
          <Reveal y={18}>
          <section className="card p-6 sm:p-8">
            <h2 className={`${sectionTitle} mb-4`}>Security</h2>
            {!user.has_password && (
              <p className="mb-4 text-sm text-white/65">
                You currently sign in via magic link. Add a password to sign in
                directly — the magic-link option stays available either way.
              </p>
            )}
            {pwMsg && (
              <p className="mb-3 text-sm text-signal-go">{pwMsg.text}</p>
            )}
            {pwTask.error && (
              <p className="mb-3 text-sm text-signal-foul">{pwTask.error}</p>
            )}
            <form
              ref={pwFormRef}
              onSubmit={(e) => {
                e.preventDefault();
                if (!pwTask.active) pwTask.run();
              }}
              className="max-w-sm space-y-3"
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
                variant="ghost"
              />
            </form>
          </section>
          </Reveal>

          {/* ── Danger zone — cancel subscription ──────────────────────── */}
          {user.tier !== "free" && (
            <Reveal y={18}>
            <section className="card border-signal-foul/20 p-6 sm:p-8">
              <h2 className={sectionTitle}>Danger zone</h2>
              {subMsg && (
                <p className="mt-3 text-sm text-signal-stage">{subMsg}</p>
              )}
              <div className="mt-4">
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
                  <>
                    <p className="text-sm text-white/55">
                      Cancelling keeps your access until the end of the current
                      billing period; after that your account moves to the Free
                      tier. Your runs and builds are retained.
                    </p>
                    <button
                      onClick={() => { setCancelOpen(true); cancelTask.reset(); }}
                      className="btn-danger btn-sm mt-3"
                    >
                      Cancel subscription
                    </button>
                  </>
                )}
              </div>
            </section>
            </Reveal>
          )}
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
