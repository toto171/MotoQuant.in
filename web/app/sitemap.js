// Sitemap, compiled into /sitemap.xml at build time (App Router convention).
//
// Everything here is known at build time; nothing is fetched from the API:
//   - bike pages: the ids in data/bike-ids.json that have a page
//     (lib/stockCatalog.js), so a removed bike never stays listed;
//   - blog posts: their own dateModified/datePublished (lib/blogDates.js);
//   - every other page: CATALOG_DATE, the date the catalog and the pages were
//     last regenerated. Bump it when they change; a build-time "now" told
//     crawlers every page changed on every deploy.

import { SITE_URL } from "./StructuredData";
import { BIKE_PAGE_IDS } from "../lib/stockCatalog";
import { BLOG_DATES } from "../lib/blogDates";

const CATALOG_DATE = new Date("2026-11-10T00:00:00Z");

function postDate(slug) {
  const d = BLOG_DATES[slug];
  if (!d) throw new Error(`sitemap: no date for blog post ${slug} (lib/blogDates.js)`);
  return new Date(`${d.modified || d.published}T00:00:00Z`);
}

// The blog index changes whenever a post does.
const LATEST_POST_DATE = new Date(
  Math.max(...Object.keys(BLOG_DATES).map((slug) => postDate(slug).getTime())),
);

export default function sitemap() {
  const staticRoutes = [
    {
      url: `${SITE_URL}/`,
      lastModified: CATALOG_DATE,
      changeFrequency: "weekly",
      priority: 1.0,
    },
    {
      url: `${SITE_URL}/simulator`,
      lastModified: CATALOG_DATE,
      changeFrequency: "weekly",
      priority: 0.9,
    },
    {
      url: `${SITE_URL}/optimize`,
      lastModified: CATALOG_DATE,
      changeFrequency: "monthly",
      priority: 0.85,
    },
    {
      url: `${SITE_URL}/autotune`,
      lastModified: CATALOG_DATE,
      changeFrequency: "monthly",
      priority: 0.85,
    },
    {
      url: `${SITE_URL}/bikes`,
      lastModified: CATALOG_DATE,
      changeFrequency: "weekly",
      priority: 0.9,
    },
    {
      url: `${SITE_URL}/leaderboard`,
      lastModified: CATALOG_DATE,
      changeFrequency: "daily",
      priority: 0.8,
    },
    {
      url: `${SITE_URL}/terms`,
      lastModified: CATALOG_DATE,
      changeFrequency: "yearly",
      priority: 0.3,
    },
    {
      url: `${SITE_URL}/privacy`,
      lastModified: CATALOG_DATE,
      changeFrequency: "yearly",
      priority: 0.3,
    },
    {
      url: `${SITE_URL}/contact`,
      lastModified: CATALOG_DATE,
      changeFrequency: "yearly",
      priority: 0.4,
    },
    {
      url: `${SITE_URL}/features`,
      lastModified: CATALOG_DATE,
      changeFrequency: "monthly",
      priority: 0.85,
    },
    {
      url: `${SITE_URL}/about`,
      lastModified: CATALOG_DATE,
      changeFrequency: "monthly",
      priority: 0.7,
    },
    {
      url: `${SITE_URL}/blog`,
      lastModified: LATEST_POST_DATE,
      changeFrequency: "weekly",
      priority: 0.8,
    },
    {
      url: `${SITE_URL}/blog/motoquant-2-0-is-open-source`,
      lastModified: postDate("motoquant-2-0-is-open-source"),
      changeFrequency: "monthly",
      priority: 0.85,
    },
    {
      url: `${SITE_URL}/blog/best-mods-for-ktm-rc-390-budget-vs-cost-per-tenth`,
      lastModified: postDate("best-mods-for-ktm-rc-390-budget-vs-cost-per-tenth"),
      changeFrequency: "monthly",
      priority: 0.86,
    },
    {
      url: `${SITE_URL}/blog/pulsar-n125-vs-raider-125-vs-glamour-125-quarter-mile-physics`,
      lastModified: postDate("pulsar-n125-vs-raider-125-vs-glamour-125-quarter-mile-physics"),
      changeFrequency: "monthly",
      priority: 0.86,
    },
    {
      url: `${SITE_URL}/blog/kawasaki-ninja-zx-4r-quarter-mile-physics`,
      lastModified: postDate("kawasaki-ninja-zx-4r-quarter-mile-physics"),
      changeFrequency: "monthly",
      priority: 0.85,
    },
    {
      url: `${SITE_URL}/blog/yamaha-xsr900-gp-vs-mt-09-quarter-mile-physics`,
      lastModified: postDate("yamaha-xsr900-gp-vs-mt-09-quarter-mile-physics"),
      changeFrequency: "monthly",
      priority: 0.82,
    },
    {
      url: `${SITE_URL}/blog/cfmoto-800nk-quarter-mile-physics`,
      lastModified: postDate("cfmoto-800nk-quarter-mile-physics"),
      changeFrequency: "monthly",
      priority: 0.82,
    },
    {
      url: `${SITE_URL}/blog/cfmoto-675sr-r-quarter-mile-physics`,
      lastModified: postDate("cfmoto-675sr-r-quarter-mile-physics"),
      changeFrequency: "monthly",
      priority: 0.85,
    },
    {
      url: `${SITE_URL}/blog/bmw-f-900-gs-quarter-mile-physics`,
      lastModified: postDate("bmw-f-900-gs-quarter-mile-physics"),
      changeFrequency: "monthly",
      priority: 0.85,
    },
    {
      url: `${SITE_URL}/blog/triumph-tiger-900-gt-pro-quarter-mile-physics`,
      lastModified: postDate("triumph-tiger-900-gt-pro-quarter-mile-physics"),
      changeFrequency: "monthly",
      priority: 0.86,
    },
    {
      url: `${SITE_URL}/blog/royal-enfield-interceptor-650-quarter-mile-physics`,
      lastModified: postDate("royal-enfield-interceptor-650-quarter-mile-physics"),
      changeFrequency: "monthly",
      priority: 0.86,
    },
    {
      url: `${SITE_URL}/blog/yamaha-rd350-quarter-mile-physics`,
      lastModified: postDate("yamaha-rd350-quarter-mile-physics"),
      changeFrequency: "monthly",
      priority: 0.86,
    },
    {
      url: `${SITE_URL}/blog/yezdi-roadster-quarter-mile-physics`,
      lastModified: postDate("yezdi-roadster-quarter-mile-physics"),
      changeFrequency: "monthly",
      priority: 0.8,
    },
    {
      url: `${SITE_URL}/blog/yamaha-mt-125-xsr125-platform-physics`,
      lastModified: postDate("yamaha-mt-125-xsr125-platform-physics"),
      changeFrequency: "monthly",
      priority: 0.78,
    },
    {
      url: `${SITE_URL}/blog/how-a-2-stroke-expansion-chamber-actually-works`,
      lastModified: postDate("how-a-2-stroke-expansion-chamber-actually-works"),
      changeFrequency: "monthly",
      priority: 0.8,
    },
    {
      url: `${SITE_URL}/blog/hayabusa-vs-zx-14r-which-is-faster`,
      lastModified: postDate("hayabusa-vs-zx-14r-which-is-faster"),
      changeFrequency: "monthly",
      priority: 0.8,
    },
    {
      url: `${SITE_URL}/blog/hayabusa-quarter-mile-physics-what-limits-9-6-seconds`,
      lastModified: postDate("hayabusa-quarter-mile-physics-what-limits-9-6-seconds"),
      changeFrequency: "monthly",
      priority: 0.88,
    },
    {
      url: `${SITE_URL}/blog/hero-xtreme-200s-4v-quarter-mile-physics`,
      lastModified: postDate("hero-xtreme-200s-4v-quarter-mile-physics"),
      changeFrequency: "monthly",
      priority: 0.78,
    },
    {
      url: `${SITE_URL}/blog/husqvarna-svartpilen-250-vs-ktm-duke-250-quarter-mile-physics`,
      lastModified: postDate("husqvarna-svartpilen-250-vs-ktm-duke-250-quarter-mile-physics"),
      changeFrequency: "monthly",
      priority: 0.8,
    },
    {
      url: `${SITE_URL}/blog/honda-cb125r-quarter-mile-physics`,
      lastModified: postDate("honda-cb125r-quarter-mile-physics"),
      changeFrequency: "monthly",
      priority: 0.78,
    },
    {
      url: `${SITE_URL}/blog/honda-cbr150r-quarter-mile-physics`,
      lastModified: postDate("honda-cbr150r-quarter-mile-physics"),
      changeFrequency: "monthly",
      priority: 0.82,
    },
    {
      url: `${SITE_URL}/blog/kawasaki-ninja-h2-sx-quarter-mile-physics`,
      lastModified: postDate("kawasaki-ninja-h2-sx-quarter-mile-physics"),
      changeFrequency: "monthly",
      priority: 0.84,
    },
    {
      url: `${SITE_URL}/blog/yamaha-mt-15-v1-quarter-mile-physics`,
      lastModified: postDate("yamaha-mt-15-v1-quarter-mile-physics"),
      changeFrequency: "monthly",
      priority: 0.82,
    },
    {
      url: `${SITE_URL}/blog/ktm-1390-super-duke-r-evo-quarter-mile-physics`,
      lastModified: postDate("ktm-1390-super-duke-r-evo-quarter-mile-physics"),
      changeFrequency: "monthly",
      priority: 0.78,
    },
    {
      url: `${SITE_URL}/blog/ktm-duke-390-vs-rc-390-quarter-mile-physics`,
      lastModified: postDate("ktm-duke-390-vs-rc-390-quarter-mile-physics"),
      changeFrequency: "monthly",
      priority: 0.84,
    },
    {
      url: `${SITE_URL}/blog/ktm-duke-390-quarter-mile-stock-to-11s`,
      lastModified: postDate("ktm-duke-390-quarter-mile-stock-to-11s"),
      changeFrequency: "monthly",
      priority: 0.86,
    },
    {
      url: `${SITE_URL}/blog/pulsar-ns200-vs-apache-rtr-200-quarter-mile-physics`,
      lastModified: postDate("pulsar-ns200-vs-apache-rtr-200-quarter-mile-physics"),
      changeFrequency: "monthly",
      priority: 0.82,
    },
    {
      url: `${SITE_URL}/blog/pulsar-ns400z-quarter-mile-physics`,
      lastModified: postDate("pulsar-ns400z-quarter-mile-physics"),
      changeFrequency: "monthly",
      priority: 0.82,
    },
    {
      url: `${SITE_URL}/blog/re-continental-gt-650-quarter-mile-physics`,
      lastModified: postDate("re-continental-gt-650-quarter-mile-physics"),
      changeFrequency: "monthly",
      priority: 0.8,
    },
    {
      url: `${SITE_URL}/blog/how-the-motoquant-physics-engine-works`,
      lastModified: postDate("how-the-motoquant-physics-engine-works"),
      changeFrequency: "monthly",
      priority: 0.78,
    },
    {
      url: `${SITE_URL}/blog/the-physics-of-a-perfect-launch`,
      lastModified: postDate("the-physics-of-a-perfect-launch"),
      changeFrequency: "monthly",
      priority: 0.75,
    },
    {
      url: `${SITE_URL}/blog/why-your-r15-wont-hit-14s`,
      lastModified: postDate("why-your-r15-wont-hit-14s"),
      changeFrequency: "monthly",
      priority: 0.75,
    },
    {
      url: `${SITE_URL}/blog/how-to-tune-for-aamby-valley-in-november`,
      lastModified: postDate("how-to-tune-for-aamby-valley-in-november"),
      changeFrequency: "monthly",
      priority: 0.75,
    },
    {
      url: `${SITE_URL}/blog/suzuki-gsx-s750-vs-ktm-890-duke-quarter-mile`,
      lastModified: postDate("suzuki-gsx-s750-vs-ktm-890-duke-quarter-mile"),
      changeFrequency: "monthly",
      priority: 0.83,
    },
    {
      url: `${SITE_URL}/blog/ktm-890-duke-r-quarter-mile-india`,
      lastModified: postDate("ktm-890-duke-r-quarter-mile-india"),
      changeFrequency: "monthly",
      priority: 0.86,
    },
    {
      url: `${SITE_URL}/blog/how-to-tune-for-mmrt-chennai`,
      lastModified: postDate("how-to-tune-for-mmrt-chennai"),
      changeFrequency: "monthly",
      priority: 0.82,
    },
    {
      url: `${SITE_URL}/blog/kawasaki-ninja-400-vs-zx-4r-quarter-mile-physics`,
      lastModified: postDate("kawasaki-ninja-400-vs-zx-4r-quarter-mile-physics"),
      changeFrequency: "monthly",
      priority: 0.84,
    },
    {
      url: `${SITE_URL}/blog/triumph-street-triple-765r-quarter-mile-physics`,
      lastModified: postDate("triumph-street-triple-765r-quarter-mile-physics"),
      changeFrequency: "monthly",
      priority: 0.85,
    },
    {
      url: `${SITE_URL}/blog/kawasaki-z900rs-quarter-mile-physics`,
      lastModified: postDate("kawasaki-z900rs-quarter-mile-physics"),
      changeFrequency: "monthly",
      priority: 0.84,
    },
    {
      url: `${SITE_URL}/blog/aprilia-tuono-660-factory-quarter-mile-physics`,
      lastModified: postDate("aprilia-tuono-660-factory-quarter-mile-physics"),
      changeFrequency: "monthly",
      priority: 0.85,
    },
    {
      url: `${SITE_URL}/blog/aprilia-tuono-457-vs-rs-457-quarter-mile-physics`,
      lastModified: postDate("aprilia-tuono-457-vs-rs-457-quarter-mile-physics"),
      changeFrequency: "monthly",
      priority: 0.85,
    },
    {
      url: `${SITE_URL}/blog/bajaj-dominar-400-quarter-mile-physics`,
      lastModified: postDate("bajaj-dominar-400-quarter-mile-physics"),
      changeFrequency: "monthly",
      priority: 0.84,
    },
    {
      url: `${SITE_URL}/blog/harley-nightster-rh975-quarter-mile-physics`,
      lastModified: postDate("harley-nightster-rh975-quarter-mile-physics"),
      changeFrequency: "monthly",
      priority: 0.85,
    },
    {
      url: `${SITE_URL}/blog/honda-hornet-2-0-vs-pulsar-ns200-quarter-mile`,
      lastModified: postDate("honda-hornet-2-0-vs-pulsar-ns200-quarter-mile"),
      changeFrequency: "monthly",
      priority: 0.84,
    },
    {
      url: `${SITE_URL}/blog/royal-enfield-bullet-350-quarter-mile-physics`,
      lastModified: postDate("royal-enfield-bullet-350-quarter-mile-physics"),
      changeFrequency: "monthly",
      priority: 0.86,
    },
    {
      url: `${SITE_URL}/blog/royal-enfield-hunter-350-quarter-mile-physics`,
      lastModified: postDate("royal-enfield-hunter-350-quarter-mile-physics"),
      changeFrequency: "monthly",
      priority: 0.87,
    },
    {
      url: `${SITE_URL}/blog/indian-drag-strip-elevation-comparison`,
      lastModified: postDate("indian-drag-strip-elevation-comparison"),
      changeFrequency: "monthly",
      priority: 0.88,
    },
    {
      url: `${SITE_URL}/blog/suzuki-gsx-r600-k8-quarter-mile-physics`,
      lastModified: postDate("suzuki-gsx-r600-k8-quarter-mile-physics"),
      changeFrequency: "monthly",
      priority: 0.84,
    },
    {
      url: `${SITE_URL}/blog/600cc-supersport-launch-physics-engine-deceleration`,
      lastModified: postDate("600cc-supersport-launch-physics-engine-deceleration"),
      changeFrequency: "monthly",
      priority: 0.86,
    },
    {
      url: `${SITE_URL}/docs`,
      lastModified: CATALOG_DATE,
      changeFrequency: "monthly",
      priority: 0.7,
    },
    {
      url: `${SITE_URL}/docs/getting-started`,
      lastModified: CATALOG_DATE,
      changeFrequency: "monthly",
      priority: 0.8,
    },
    {
      url: `${SITE_URL}/docs/glossary`,
      lastModified: CATALOG_DATE,
      changeFrequency: "monthly",
      priority: 0.8,
    },
    {
      url: `${SITE_URL}/docs/physics`,
      lastModified: CATALOG_DATE,
      changeFrequency: "monthly",
      priority: 0.8,
    },
    {
      url: `${SITE_URL}/docs/validation`,
      lastModified: CATALOG_DATE,
      changeFrequency: "monthly",
      priority: 0.8,
    },
    {
      url: `${SITE_URL}/whitepaper`,
      lastModified: CATALOG_DATE,
      changeFrequency: "monthly",
      priority: 0.85,
    },
    {
      url: `${SITE_URL}/validation`,
      lastModified: CATALOG_DATE,
      changeFrequency: "monthly",
      priority: 0.85,
    },
  ];

  const bikeRoutes = BIKE_PAGE_IDS.map((id) => ({
    url: `${SITE_URL}/bikes/${id}`,
    lastModified: CATALOG_DATE,
    changeFrequency: "monthly",
    priority: 0.6,
  }));

  return [...staticRoutes, ...bikeRoutes];
}
