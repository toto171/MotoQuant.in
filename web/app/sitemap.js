// Dynamic sitemap — Next.js 14 App Router convention.
// Compiled into /sitemap.xml at build time.

import { SITE_URL } from "./StructuredData";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ||
  process.env.MOTOQUANT_INTERNAL_API_URL ||
  SITE_URL;

export const revalidate = 86400;

async function fetchAllBikes() {
  try {
    const res = await fetch(`${API_BASE}/api/bikes?limit=500`, {
      next: { revalidate: 86400 },
    });
    if (!res.ok) throw new Error(`Sitemap bike fetch: ${res.status}`);
    const data = await res.json();
    return Array.isArray(data.bikes) ? data.bikes : [];
  } catch (err) {
    if (process.env.NODE_ENV !== "production") {
      console.warn("[sitemap] API unreachable, using ID range fallback:", err);
    }
    return Array.from({ length: 310 }, (_, i) => ({ id: i + 1 }));
  }
}

export default async function sitemap() {
  const now = new Date();
  const bikes = await fetchAllBikes();

  const staticRoutes = [
    {
      url: `${SITE_URL}/`,
      lastModified: now,
      changeFrequency: "weekly",
      priority: 1.0,
    },
    {
      url: `${SITE_URL}/simulator`,
      lastModified: now,
      changeFrequency: "weekly",
      priority: 0.9,
    },
    {
      url: `${SITE_URL}/bikes`,
      lastModified: now,
      changeFrequency: "weekly",
      priority: 0.9,
    },
    {
      url: `${SITE_URL}/features`,
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.85,
    },
    {
      url: `${SITE_URL}/about`,
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.7,
    },
    {
      url: `${SITE_URL}/pricing`,
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.85,
    },
    {
      url: `${SITE_URL}/blog`,
      lastModified: now,
      changeFrequency: "weekly",
      priority: 0.8,
    },
    {
      url: `${SITE_URL}/blog/best-mods-for-ktm-rc-390-budget-vs-cost-per-tenth`,
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.86,
    },
    {
      url: `${SITE_URL}/blog/kawasaki-ninja-zx-4r-quarter-mile-physics`,
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.85,
    },
    {
      url: `${SITE_URL}/blog/yamaha-xsr900-gp-vs-mt-09-quarter-mile-physics`,
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.82,
    },
    {
      url: `${SITE_URL}/blog/cfmoto-800nk-quarter-mile-physics`,
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.82,
    },
    {
      url: `${SITE_URL}/blog/yezdi-roadster-quarter-mile-physics`,
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.8,
    },
    {
      url: `${SITE_URL}/blog/yamaha-mt-125-xsr125-platform-physics`,
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.78,
    },
    {
      url: `${SITE_URL}/blog/how-a-2-stroke-expansion-chamber-actually-works`,
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.8,
    },
    {
      url: `${SITE_URL}/blog/hayabusa-vs-zx-14r-which-is-faster`,
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.8,
    },
    {
      url: `${SITE_URL}/blog/hero-xtreme-200s-4v-quarter-mile-physics`,
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.78,
    },
    {
      url: `${SITE_URL}/blog/ktm-1390-super-duke-r-evo-quarter-mile-physics`,
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.78,
    },
    {
      url: `${SITE_URL}/blog/ktm-duke-390-vs-rc-390-quarter-mile-physics`,
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.84,
    },
    {
      url: `${SITE_URL}/blog/pulsar-ns200-vs-apache-rtr-200-quarter-mile-physics`,
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.82,
    },
    {
      url: `${SITE_URL}/blog/pulsar-ns400z-quarter-mile-physics`,
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.82,
    },
    {
      url: `${SITE_URL}/blog/re-continental-gt-650-quarter-mile-physics`,
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.8,
    },
    {
      url: `${SITE_URL}/blog/how-the-motoquant-physics-engine-works`,
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.78,
    },
    {
      url: `${SITE_URL}/blog/the-physics-of-a-perfect-launch`,
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.75,
    },
    {
      url: `${SITE_URL}/blog/why-your-r15-wont-hit-14s`,
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.75,
    },
    {
      url: `${SITE_URL}/blog/how-to-tune-for-aamby-valley-in-november`,
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.75,
    },
    {
      url: `${SITE_URL}/blog/suzuki-gsx-s750-vs-ktm-890-duke-quarter-mile`,
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.83,
    },
    {
      url: `${SITE_URL}/blog/ktm-890-duke-r-quarter-mile-india`,
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.86,
    },
    {
      url: `${SITE_URL}/blog/how-to-tune-for-mmrt-chennai`,
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.82,
    },
    {
      url: `${SITE_URL}/blog/kawasaki-ninja-400-vs-zx-4r-quarter-mile-physics`,
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.84,
    },
    {
      url: `${SITE_URL}/blog/triumph-street-triple-765r-quarter-mile-physics`,
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.85,
    },
    {
      url: `${SITE_URL}/blog/kawasaki-z900rs-quarter-mile-physics`,
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.84,
    },
    {
      url: `${SITE_URL}/docs/getting-started`,
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.8,
    },
    {
      url: `${SITE_URL}/docs/physics`,
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.8,
    },
    {
      url: `${SITE_URL}/docs/validation`,
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.8,
    },
    {
      url: `${SITE_URL}/whitepaper`,
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.85,
    },
  ];

  const bikeRoutes = bikes.map((bike) => ({
    url: `${SITE_URL}/bikes/${bike.id}`,
    lastModified: now,
    changeFrequency: "monthly",
    priority: 0.6,
  }));

  return [...staticRoutes, ...bikeRoutes];
}
