/** @type {import('next').NextConfig} */
const nextConfig = {
  // ─── API proxy (same-origin → Render backend) ──────────────────────────
  // web/lib/api.js sets API_URL='' so every fetch becomes same-origin
  // (`/api/...`).  This rewrite forwards them to the Render backend.
  // Two reasons we proxy server-side instead of letting the browser hit
  // Render directly:
  //   1. DNS filters on hostel/college/corporate WiFi routinely block
  //      PaaS wildcard domains (they host unmoderated user projects,
  //      common DNS-block target — we hit this on the previous Railway
  //      host). Proxying via motoquant.in means only Vercel's edge needs
  //      to resolve the backend host.
  //   2. No CORS — it's all same-origin from the browser's view.
  //
  // Override locally with NEXT_PUBLIC_API_URL=http://localhost:8000 in
  // web/.env.local (web/lib/api.js will use that absolute URL instead
  // of relying on this rewrite).
  async rewrites() {
    const backend =
      process.env.MOTOQUANT_API_BACKEND ||
      'https://motoquant-api.onrender.com';
    return [
      {
        source: '/api/:path*',
        destination: `${backend}/api/:path*`,
      },
    ];
  },

  // ─── Cache headers for /public assets ──────────────────────────────────
  // /surrogate/{model,bikes}.json (~330 KB pair, fetched by lib/surrogate.js
  // on every simulator boot) only change on a surrogate regen, so an hour of
  // freshness + a day of stale-while-revalidate kills the repeat-visit
  // transfer. Safe to serve stale: surrogate.js fingerprint-checks the pair
  // and falls back to the server sim path on any mismatch. Nothing else in
  // /public is content-hashed (Next already stamps /_next/static/* immutable
  // itself), so no immutable rule here.
  async headers() {
    return [
      {
        source: '/surrogate/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=3600, stale-while-revalidate=86400',
          },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
