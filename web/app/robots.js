/**
 * MotoQuant — robots.txt route
 * =================================
 * Generates /robots.txt via the Next.js metadata convention (returned as a
 * MetadataRoute.Robots object).
 *
 * THIS IS THE ONLY SOURCE OF CRAWLER POLICY. `public/robots.txt` was deleted
 * on 2026-08-08: in the App Router a static file in public/ WINS over the
 * route handler of the same name, so the static copy silently shadowed this
 * file and the Disallow of /account, /login and /signup never reached a
 * single crawler. Do not re-add public/robots.txt.
 *
 * Two deliberate design rules, both learned from the file this replaced:
 *
 *  1. NO per-engine "Allow: /" groups. robots.txt matching is winner-take-all
 *     — a crawler obeys the single most specific User-agent group and ignores
 *     `*` entirely. The old static file gave Googlebot, Bingbot, GPTBot,
 *     ClaudeBot &c. their own bare `Allow: /` group, which granted them
 *     nothing the `*` group did not already grant while quietly exempting
 *     them from every Disallow below it. Search and LLM crawlers stay welcome
 *     (that is the point of `*: allow /`); they simply inherit the same
 *     handful of exclusions as everyone else.
 *
 *  2. Blocked scrapers each need their own group, because a Disallow only
 *     applies to the group it sits in.
 */

export const dynamic = 'force-static';

// SEO-spam and aggressive commercial scrapers. These refer no traffic; their
// requests are pure cost on a free-tier backend.
const BLOCKED_CRAWLERS = [
  'AhrefsBot',
  'SemrushBot',
  'MJ12bot',
  'DotBot',
  'PetalBot',
  'BLEXBot',
  'DataForSeoBot',
  'SeekportBot',
  'ZoominfoBot',
  'SerpstatBot',
];

export default function robots() {
  return {
    rules: [
      {
        userAgent: '*',
        allow: '/',
        // Private user pages + server internals. Every crawler that is not
        // explicitly blocked below matches this group, so this is the list
        // that actually ships.
        disallow: [
          '/account',
          '/login',
          '/signup',
          '/api/',
          '/_next/',
          '/_vercel/',
        ],
      },
      ...BLOCKED_CRAWLERS.map((userAgent) => ({ userAgent, disallow: '/' })),
    ],
    // Apex domain — every canonical URL + SITE_URL on the site uses the apex
    // (https://motoquant.in); the old www values here were the odd ones out.
    sitemap: 'https://motoquant.in/sitemap.xml',
    host: 'https://motoquant.in',
  };
}
