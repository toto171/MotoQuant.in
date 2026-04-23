// Single source of truth for the API base URL.
//
// In production we deliberately default to the *empty string* so every
// fetch becomes same-origin (`/api/bikes`, `/api/simulate/quick`, etc.)
// and gets routed via a Vercel rewrite in `vercel.json` to the Railway
// backend. This has two advantages over hitting Railway directly from
// the browser:
//
//   1. DNS filters on corporate / college / hostel WiFi routinely block
//      `*.up.railway.app` wholesale (Railway hosts unmoderated user
//      projects so it's a common target). The user's Windows resolver
//      was returning REFUSED for our Railway subdomain, which surfaced
//      as "Failed to fetch" / NXDOMAIN in the browser despite the
//      backend being perfectly healthy. Routing via motoquant.in means
//      only Vercel's edge needs to resolve Railway, which it always can.
//   2. No more CORS -- it's all same-origin. We can drop
//      `allow_origins=['*']` from the FastAPI side later.
//
// For local dev, put `NEXT_PUBLIC_API_URL=http://localhost:8000` in
// `web/.env.local` so the fetches go to your local uvicorn.
export const API_URL = process.env.NEXT_PUBLIC_API_URL || '';
