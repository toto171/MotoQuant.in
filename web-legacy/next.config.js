/** @type {import('next').NextConfig} */
const nextConfig = {
  // ─── API proxy (same-origin → Railway backend) ────────────────────────
  // web/lib/api.js sets API_URL='' so every fetch becomes same-origin
  // (`/api/...`).  This rewrite forwards them to the Railway backend.
  // Two reasons we proxy server-side instead of letting the browser hit
  // Railway directly:
  //   1. DNS filters on hostel/college/corporate WiFi routinely block
  //      `*.up.railway.app` wholesale (Railway hosts unmoderated user
  //      projects, common DNS-block target). Proxying via motoquant.in
  //      means only Vercel's edge needs to resolve Railway.
  //   2. No CORS — it's all same-origin from the browser's view.
  //
  // Override locally with NEXT_PUBLIC_API_URL=http://localhost:8000 in
  // web/.env.local (web/lib/api.js will use that absolute URL instead
  // of relying on this rewrite).
  async rewrites() {
    const backend =
      process.env.MOTOQUANT_API_BACKEND ||
      'https://web-production-de6eb.up.railway.app';
    return [
      {
        source: '/api/:path*',
        destination: `${backend}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
