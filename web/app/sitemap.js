// Dynamic sitemap — Next.js 14 App Router convention. This file is compiled
// into `/sitemap.xml` at build time (plus optional ISR revalidate).
//
// Why this matters for SEO:
//   * Google / Bing use sitemaps as the primary discovery channel for deep
//     URLs. Without one, the 287 /bikes/[id] pages get crawled slowly via
//     breadth-first link-following and many never make it into the index.
//   * Each <url> entry carries <lastmod> + <changefreq> + <priority>. Google
//     ignores priority/changefreq, but Yandex and Baidu honour them — which
//     matters for Indian SERPs where Yandex occasionally appears.
//
// Robustness: we fetch the bike catalog from the backend. If the API is
// unreachable at build time (common when deploying to Vercel before the
// Railway backend is warm), we fall back to a conservative 300-URL range
// so the sitemap is still valid and we still pick up ~all bikes.

import { SITE_URL } from './StructuredData';

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ||
  process.env.MOTOQUANT_INTERNAL_API_URL ||
  SITE_URL;

// Revalidate the sitemap every 24h in production (ISR). New bikes added to
// the catalog show up within a day without a redeploy.
export const revalidate = 86400;

async function fetchAllBikes() {
  try {
    // Catalog is 287 bikes; pull in one shot with a generous limit.
    const res = await fetch(`${API_BASE}/api/bikes?limit=500`, {
      next: { revalidate: 86400 },
    });
    if (!res.ok) throw new Error(`Sitemap bike fetch: ${res.status}`);
    const data = await res.json();
    return Array.isArray(data.bikes) ? data.bikes : [];
  } catch (err) {
    // Don't blow up the build; fall back to sequential IDs 1..310 which
    // covers the current catalog with headroom. Google will 404-prune the
    // gaps on crawl without penalising us.
    if (process.env.NODE_ENV !== 'production') {
      console.warn('[sitemap] API unreachable, using ID range fallback:', err);
    }
    return Array.from({ length: 310 }, (_, i) => ({ id: i + 1 }));
  }
}

export default async function sitemap() {
  const now = new Date();
  const bikes = await fetchAllBikes();

  /** @type {import('next').MetadataRoute.Sitemap} */
  const staticRoutes = [
    {
      url: `${SITE_URL}/`,
      lastModified: now,
      changeFrequency: 'weekly',
      priority: 1.0,
    },
    {
      url: `${SITE_URL}/simulator`,
      lastModified: now,
      changeFrequency: 'weekly',
      priority: 0.9,
    },
    {
      url: `${SITE_URL}/bikes`,
      lastModified: now,
      changeFrequency: 'weekly',
      priority: 0.9,
    },
    { url: `${SITE_URL}/features`,      lastModified: now, changeFrequency: 'monthly', priority: 0.85 },
    { url: `${SITE_URL}/about`,         lastModified: now, changeFrequency: 'monthly', priority: 0.70 },
    { ur