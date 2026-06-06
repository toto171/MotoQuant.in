/**
 * GET /api/wake — Vercel-cron-driven waker for the Render backend.
 *
 * Third keep-alive layer (2026-06-07), independent of GitHub's throttled
 * Actions cron: Vercel Hobby crons fire once a day per schedule with ±59 min
 * precision, which is exactly what the architecture needs — one reliable
 * morning wake, after which motoquant/keepwarm.py holds the service warm
 * for the rest of the UTC 0-18 active window.
 *
 * This is a real Next.js route handler (filesystem routes win over the
 * /api/* rewrite, so it is NOT proxied to Render) that fetches the Render
 * health URL directly. If the fetch times out mid-cold-start that is fine:
 * the request reaching Render is what triggers the boot — the instance
 * keeps booting after we hang up, and the in-app loop takes over from
 * startup. Always returns 200 with diagnostics so cron history stays
 * readable (a slow cold start is not a failure).
 *
 * Schedules live in vercel.json ("crons"): 00:05, 07:00 and 12:00 UTC —
 * morning wake (~5:35 AM IST) plus midday and evening-peak safety nets.
 */

export const dynamic = 'force-dynamic';
export const maxDuration = 60; // Hobby plan ceiling

const RENDER_HEALTH_URL = 'https://motoquant-api.onrender.com/api/health';

export async function GET() {
  const startedAt = Date.now();
  let status = null;
  let body = null;
  let error = null;
  try {
    const res = await fetch(RENDER_HEALTH_URL, {
      cache: 'no-store',
      signal: AbortSignal.timeout(55_000),
      headers: { 'User-Agent': 'motoquant-vercel-wake/1.0' },
    });
    status = res.status;
    try {
      body = await res.json();
    } catch {
      body = null;
    }
  } catch (e) {
    // Timeout during a cold start still means the wake was delivered.
    error = String(e?.message || e);
  }
  return Response.json({
    woke: true,
    upstream_status: status,
    upstream: body,
    error,
    elapsed_ms: Date.now() - startedAt,
  });
}
