"use client";

/**
 * MotoQuant — Account Page
 * ==========================
 * Displays: email, saved-run garage, password management, sign out.
 * Requires authentication — redirects to /login if not signed in.
 *
 * IGNITION v5 (July 2026): PageHero ("Your garage") + stacked `.card`
 * sections — Profile, Garage (bike names in display face, ETs mono, venue
 * chips, rows link to /r/[id]), Security. ActionButton + useAsyncTask on the
 * password submit so the button itself is the progress bar.
 *
 * October 2026: MotoQuant is free and open source — the tier badge,
 * subscription status, license-key seats, cancel-subscription danger zone
 * and post-checkout banner were removed with the payment stack. Accounts
 * remain optional and exist only to keep a garage of saved runs.
 */

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../../components/AuthProvider";
import SiteNav from "../../components/SiteNav";
import SiteFooter from "../../components/SiteFooter";
import PageHero from "../../components/PageHero";
import { Reveal } from "../../components/Reveal";
import ActionButton from "../../components/ActionButton";
import { SkeletonCard, SkeletonTable } from "../../components/Skeleton";
import useAsyncTask from "../../lib/useAsyncTask";

import { API_URL_DIRECT as API_BASE } from "../../lib/api";
import { CONTACT_EMAIL } from "../../lib/site";

export default function AccountPage() {
  const router = useRouter();
  const { user, accessToken, isLoading, isAuthenticated, logout, refetchUser } = useAuth();

  const [pwCurrent, setPwCurrent] = useState("");
  const [pwNew, setPwNew] = useState("");
  const [pwMsg, setPwMsg] = useState(null); // { tone: 'ok', text } — errors live on pwTask.error
  const [runs, setRuns] = useState([]);
  const [runsLoading, setRunsLoading] = useState(false);
  const pwFormRef = useRef(null);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.replace("/login");
  }, [isLoading, isAuthenticated, router]);

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

  // ── async task (the button is the progress bar) ──────────────────────

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

  const sectionTitle =
    "font-display font-semibold text-lg md:text-xl text-white";

  return (
    <div className="min-h-screen bg-asphalt-0 text-white">
      <SiteNav />
      <PageHero
        align="center"
        kicker="account"
        title={<>Your <span className="text-accent">garage</span></>}
        sub="Saved runs and sign-in settings for your MotoQuant account."
      />
      <main id="main" className="pb-20 px-4 sm:px-6">
        <div className="mx-auto max-w-3xl space-y-6">
          {/* ── Profile ───────────────────────────────────────────────── */}
          <Reveal y={18}>
          <section className="card p-6 sm:p-8">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <h2 className={sectionTitle}>Profile</h2>
                <p className="mt-3 font-medium text-white">{user.email}</p>
                <p className="mt-1 text-sm text-white/55">
                  {user.email_verified ? "Email verified · " : ""}
                  Every feature is free &mdash; there are no plans or tiers.
                </p>
              </div>
              <button onClick={logout} className="btn-ghost btn-sm">
                Sign out
              </button>
            </div>
            <p className="mt-5 text-xs text-white/45">
              Want your account and saved runs deleted? Email{" "}
              <a
                href={`mailto:${CONTACT_EMAIL}?subject=Delete%20my%20account`}
                className="text-white/70 underline decoration-white/25 underline-offset-2 hover:text-white transition-colors"
              >
                {CONTACT_EMAIL}
              </a>{" "}
              from this address.
            </p>
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
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
