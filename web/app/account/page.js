"use client";

/**
 * MotoQuant — Account Page
 * ==============================
 * Displays: email, saved-run garage, password management. Accounts are
 * optional and exist only to save runs — there are no tiers or plans.
 * Requires authentication — redirects to /login if not signed in.
 *
 * v6 (CLARITY): PageHeader ("Your saved runs"), then compact `.card`
 * sections — account, saved runs (rows link to /r/[id]) and password.
 * ActionButton + useAsyncTask on every submit so the button is the
 * progress bar.
 */

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../../components/AuthProvider";
import SiteNav from "../../components/SiteNav";
import SiteFooter from "../../components/SiteFooter";
import PageHeader from "../../components/PageHeader";
import Link from "next/link";
import ActionButton from "../../components/ActionButton";
import { SkeletonCard, SkeletonTable } from "../../components/Skeleton";
import useAsyncTask from "../../lib/useAsyncTask";

import { API_URL_DIRECT as API_BASE } from "../../lib/api";

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

  // ── async tasks (one per submit — the button is the progress bar) ──────

  const pwTask = useAsyncTask(async (signal) => {
    setPwMsg(null);
    if (pwNew.length < 8) {
      throw new Error("Choose a new password with at least 8 characters.");
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
        typeof data.detail === "string" ? data.detail : "We couldn't update your password. Check your current password and try again."
      );
    }
    setPwMsg({ tone: "ok", text: "Your password has been updated." });
    setPwCurrent("");
    setPwNew("");
    refetchUser();
    return true;
  });

  if (isLoading || !user) {
    return (
      <div className="min-h-screen bg-asphalt-0 text-white">
        <SiteNav />
        <main id="main" className="pt-28 pb-20 px-4 sm:px-6">
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
      <PageHeader
        title="Your saved runs"
        lede="Runs you save while signed in appear here. Each one has a page you can share."
        maxWidth="max-w-3xl"
      />
      <main id="main" className="pb-20 px-4 sm:px-6">
        <div className="mx-auto max-w-3xl space-y-6">
          {/* ── Profile ─────────────────────────────────────────────────── */}
                    <section className="card p-6 sm:p-8">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <h2 className={sectionTitle}>Your account</h2>
                <p className="mt-2 text-base text-white/80">{user.email}</p>
              </div>
              <div className="flex items-center gap-3">
                <button onClick={logout} className="btn-ghost btn-sm">
                  Sign out
                </button>
              </div>
            </div>

          </section>
          
          {/* ── Garage — saved runs ────────────────────────────────────── */}
                    <section className="card p-6 sm:p-8">
            <div className="mb-5 flex items-center justify-between">
              <h2 className={sectionTitle}>Your saved runs</h2>
              <Link href="/simulator" className="btn-ghost btn-sm">
                Open the simulator
              </Link>
            </div>
            {runsLoading && (
              <SkeletonTable rows={4} cols={4} aria-label="Loading your saved runs" />
            )}
            {!runsLoading && runs.length === 0 && (
              <p className="text-sm text-white/65">
                You haven&apos;t saved any runs yet. Calculate a time in the simulator
                and choose <strong className="text-white">Save this run</strong> while
                you&apos;re signed in. It will show up here.
              </p>
            )}
            {!runsLoading && runs.length > 0 && (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-white/10 text-left text-white/60">
                      <th className="py-2 pr-4 font-medium">Bike</th>
                      <th className="py-2 pr-4 text-right font-medium">Quarter-mile time</th>
                      <th className="py-2 pr-4 text-right font-medium">Finish-line speed</th>
                      <th className="hidden py-2 pr-4 font-medium sm:table-cell">Venue</th>
                      <th className="hidden py-2 font-medium sm:table-cell">Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {runs.map((r) => (
                      <tr key={r.id} className="border-b border-white/5">
                        <td className="py-2.5 pr-4">
                          <Link
                            href={`/r/${r.id}`}
                            className="font-display font-semibold text-white/90 hover:text-white transition-colors"
                          >
                            {r.manufacturer ? `${r.manufacturer} ${r.model}` : `Run #${r.id}`}
                          </Link>
                        </td>
                        <td className="py-2.5 pr-4 text-right font-mono tabular-nums font-medium text-white">
                          {r.et_quarter_s != null ? `${r.et_quarter_s.toFixed(3)} s` : ""}
                        </td>
                        <td className="py-2.5 pr-4 text-right font-mono tabular-nums text-white/70">
                          {r.trap_speed_kmh != null ? `${r.trap_speed_kmh.toFixed(1)} km/h` : ""}
                        </td>
                        <td className="hidden py-2.5 pr-4 sm:table-cell">
                          {r.venue ? <span className="chip">{r.venue}</span> : null}
                        </td>
                        <td className="hidden py-2.5 text-sm text-white/60 sm:table-cell">
                          {r.created_at ? new Date(r.created_at).toLocaleDateString() : ""}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
          
          {/* ── Security — password ────────────────────────────────────── */}
                    <section className="card p-6 sm:p-8">
            <h2 className={`${sectionTitle} mb-4`}>Password</h2>
            {!user.has_password && (
              <p className="mb-4 text-sm text-white/65">
                You currently sign in with an emailed link. Add a password if you&apos;d
                rather sign in directly. The emailed link still works either way.
              </p>
            )}
            {pwMsg && (
              <p role="status" className="mb-3 text-sm text-signal-go">{pwMsg.text}</p>
            )}
            {pwTask.error && (
              <p role="alert" className="mb-3 text-sm text-signal-foul">{pwTask.error}</p>
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
                <div>
                  <label htmlFor="pw-current" className="field-label">Current password</label>
                  <input
                    id="pw-current"
                    type="password"
                    autoComplete="current-password"
                    required
                    value={pwCurrent}
                    onChange={(e) => setPwCurrent(e.target.value)}
                    className="input-base"
                  />
                </div>
              )}
              <div>
                <label htmlFor="pw-new" className="field-label">New password</label>
                <input
                  id="pw-new"
                  type="password"
                  autoComplete="new-password"
                  required
                  minLength={8}
                  value={pwNew}
                  onChange={(e) => setPwNew(e.target.value)}
                  className="input-base"
                />
                <p className="field-hint">At least 8 characters.</p>
              </div>
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
                  </div>
      </main>
      <SiteFooter />
    </div>
  );
}
