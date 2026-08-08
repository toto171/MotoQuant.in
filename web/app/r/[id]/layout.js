// Server layout for /r/[id] — public shareable run pages.
//
// Every saved sim run gets a permanent, crawlable URL with unique OG
// metadata, so a shared timeslip unfurls with the bike + ET in WhatsApp /
// X / Telegram previews. This is the viral loop: share → preview card →
// "Simulate your own" CTA.

import { SITE_URL } from '../../StructuredData';
import { serverApiBase } from '../../../lib/api';

const API_BASE = serverApiBase(SITE_URL);

async function fetchRun(id) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 20_000);
  try {
    const res = await fetch(`${API_BASE}/api/runs/${id}`, {
      // Saved runs are immutable — cache aggressively.
      next: { revalidate: 86400 },
      signal: controller.signal,
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  } finally {
    clearTimeout(timeout);
  }
}

export async function generateMetadata({ params }) {
  // Next 15: `params` is a Promise — await before reading. (This route is
  // dynamic, so `next build` never executes this function and cannot catch
  // a sync access; the sibling /bikes/[id]/layout.js already awaits.)
  const { id } = await params;
  const run = await fetchRun(id);
  if (!run) {
    return {
      title: 'Simulated Run | MotoQuant',
      robots: { index: false },
    };
  }
  const bike = [run.manufacturer, run.model].filter(Boolean).join(' ') || 'Motorcycle';
  const et = run.et_quarter_s ? Number(run.et_quarter_s).toFixed(3) : '—';
  const trap = run.trap_speed_kmh ? `${Number(run.trap_speed_kmh).toFixed(1)} km/h` : '';
  const title = `${bike} — ${et}s quarter mile | MotoQuant timeslip`;
  const description = `Simulated quarter-mile: ${bike} ran ${et}s${trap ? ` @ ${trap} trap` : ''}${
    run.venue ? ` at ${run.venue}` : ''
  }. RK4 physics, real conditions. Run your own build on MotoQuant.`;
  return {
    title,
    description,
    alternates: { canonical: `/r/${id}` },
    openGraph: {
      title,
      description,
      url: `${SITE_URL}/r/${id}`,
      type: 'article',
    },
    twitter: { card: 'summary_large_image', title, description },
  };
}

export default function RunLayout({ children }) {
  return children;
}
