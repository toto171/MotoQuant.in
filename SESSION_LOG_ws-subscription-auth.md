# SESSION LOG — ws/subscription-auth
**Date:** April 24, 2026  
**Workstream:** Subscription, Auth & Commercial-Launch Plumbing  
**Status:** ✅ Complete — all 8 tasks done

---

## Files Created / Modified

| File | Action | Notes |
|---|---|---|
| `motoquant/database/schema.py` | Modified | Added 5 new tables (users, sessions, magic_links, subscriptions, license_keys) with indexes |
| `motoquant/database/users_repo.py` | **New** | CRUD for users, sessions, magic_links |
| `motoquant/database/subscriptions_repo.py` | **New** | Subscription lifecycle + license key CRUD |
| `motoquant/auth.py` | **New** | FastAPI router: magic-link, verify, refresh, logout, me. `require_tier()` dependency |
| `motoquant/subscriptions.py` | **New** | FastAPI router: checkout, webhook, license-key CRUD, cancel, status |
| `motoquant/api.py` | Modified | Added `Depends` import; `require_tier` early import stub; tier guards on 3 routes; router mounts at bottom |
| `requirements-api.txt` | Modified | Added python-jose[cryptography], passlib[bcrypt], razorpay |
| `web/components/AuthProvider.js` | **New** | React context: in-memory JWT, silent refresh, sessionStorage for refresh token |
| `web/components/TierBadge.js` | **New** | Pill badge + UpgradeCTA component |
| `web/app/pricing/page.js` | **New** | Full pricing page: 3-tier matrix, monthly/yearly toggle, Razorpay checkout CTA, FAQ |
| `web/app/login/page.js` | **New** | Magic-link login + auto-verify from `?token=` param |
| `web/app/signup/page.js` | **New** | Redirects to /login (signup = same flow) |
| `web/app/account/page.js` | **New** | Account dashboard: tier, sub status, license key generate/revoke |
| `web/app/terms/page.js` | **New** | Terms of Service (Indian law, Pune jurisdiction) |
| `web/app/privacy/page.js` | **New** | Privacy Policy (data residency, right to delete, cookies) |
| `tests/test_auth.py` | **New** | 23 tests: user CRUD, magic link lifecycle, session management, JWT helpers, require_tier, rate limit |
| `tests/test_subscriptions.py` | **New** | 17 tests: subscription repo, license key quota/revoke, webhook tier upgrade/downgrade |

---

## Environment Variables Required (Production)

Set these in the Railway service dashboard before deploying:

### Auth
```
JWT_SECRET=<generate: python -c "import secrets; print(secrets.token_hex(32))">
JWT_ALGORITHM=HS256
```

### Email delivery (choose one backend)
```
# Dev mode (default — prints token to server stdout):
MOTOQUANT_EMAIL_BACKEND=stdout

# Production — SMTP (e.g. Zoho, Postmark, SES):
SMTP_HOST=smtp.postmarkapp.com
SMTP_PORT=587
SMTP_USER=<api-token>
SMTP_PASS=<api-token>
SMTP_FROM=noreply@motoquant.in

# OR — Resend.com (add resend SDK to requirements if switching):
RESEND_API_KEY=re_...
SMTP_FROM=noreply@motoquant.in
```

### Razorpay
```
RAZORPAY_KEY_ID=rzp_live_...
RAZORPAY_KEY_SECRET=<secret>
RAZORPAY_WEBHOOK_SECRET=<from Razorpay dashboard webhook settings>
```

### Razorpay Plan IDs (create plans in Razorpay dashboard first)
```
PLAN_ID_PRO_MONTHLY=plan_...
PLAN_ID_PRO_YEARLY=plan_...
PLAN_ID_STUDIO_MONTHLY=plan_...
PLAN_ID_STUDIO_YEARLY=plan_...
```

### Frontend
```
# In Vercel dashboard (web environment variables):
NEXT_PUBLIC_API_URL=https://web-production-de6eb.up.railway.app
MOTOQUANT_BASE_URL=https://www.motoquant.in
```

---

## Razorpay Setup Steps (Manual — before first deploy)

1. **Create a Razorpay account** at dashboard.razorpay.com (use Live mode for prod)
2. **Create 4 plans** under Products → Subscriptions → Plans:
   - `MotoQuant Pro Monthly` → ₹499 / 1 month / Auto-recurring
   - `MotoQuant Pro Yearly`  → ₹4,999 / 12 months / Auto-recurring
   - `MotoQuant Studio Monthly` → ₹2,999 / 1 month / Auto-recurring
   - `MotoQuant Studio Yearly`  → ₹29,999 / 12 months / Auto-recurring
   - Copy the `plan_XXXX` IDs into the env vars above
3. **Configure webhook** under Settings → Webhooks:
   - URL: `https://web-production-de6eb.up.railway.app/api/subscriptions/webhook`
   - Events to enable: `subscription.activated`, `subscription.charged`, `subscription.halted`, `subscription.cancelled`, `subscription.completed`, `subscription.authenticated`
   - Copy the webhook secret into `RAZORPAY_WEBHOOK_SECRET`
4. **GST configuration**: In Razorpay → Settings → Tax → add 18% GST (IGST for interstate)
5. **Test mode first**: Repeat steps 2-4 with `rzp_test_...` keys and test a subscription end-to-end before switching to live keys

---

## Schema Migration Path

The new auth tables use `CREATE TABLE IF NOT EXISTS` so they are **safe to run against an existing motoquant.db** — the tables are simply created on first connection if absent.

The tables are added to `TABLES_DDL` in `schema.py` (applied on `db.initialize()`) AND the `ensure_tables()` functions in each repo (belt-and-braces — called at startup by the auth router).

**To apply on the existing Railway DB:**  
1. Either push the code and let Railway auto-restart (the `ensure_tables()` call in `auth.py`'s `request_magic_link` will create tables on first request)
2. Or run once: `python -c "from motoquant.database.connection import connect; from motoquant.database.users_repo import ensure_tables; from motoquant.database.subscriptions_repo import ensure_tables as es; c=connect(); ensure_tables(c); es(c); print('done')"`

---

## Tier Gating Applied

| Route | Required Tier | Status |
|---|---|---|
| `POST /api/simulate/save` | pro | ✅ applied |
| `POST /api/calibrate/dragy` | studio | ✅ applied |
| `POST /api/calibrate/dyno` | studio | ✅ applied |
| `GET /api/analysis/*` | pro | ⚠️ Not yet applied — analysis routes not found in api.py (may be in a separate router or CLI-only). Apply `Depends(require_tier("pro"))` when adding analysis API routes |
| `POST /api/surrogate/predict` | pro | ⏳ Deferred — route not yet added (see Stream 4 / Phase 4 Remaining). Add `Depends(require_tier("pro"))` when this route is created |

---

## Architecture Decisions

### JWT in-memory only (no httpOnly cookie)
Chose JWT in React `sessionStorage` (not `localStorage` or `httpOnly cookie`) because:
- The API is hosted on a different origin (Railway) from the frontend (Vercel) — cross-origin `httpOnly` cookies require careful CORS + SameSite config
- `sessionStorage` is cleared on tab close, limiting exposure window
- Access token TTL is 15 minutes; refresh is 30 days

**Future option:** Switch to `httpOnly` cookie pattern if both API and frontend are served from the same domain.

### Magic-link email (no password)
- Simpler UX for the Indian drag community (no password to forget)
- No password-hash storage → smaller attack surface
- Magic-link tokens are SHA-256 hashed before storage (plaintext never persisted)

### SQLite → Postgres migration path
The auth tables use the same SQLite-first approach as the rest of the codebase.
When migrating to Postgres (Phase 6):
1. Export: `sqlite3 motoquant.db .dump | grep -E "INSERT INTO (users|sessions|subscriptions|license_keys|magic_links)" > auth_seed.sql`
2. Adjust types: `INTEGER PRIMARY KEY AUTOINCREMENT` → `SERIAL PRIMARY KEY`; `TEXT` dates → `TIMESTAMP WITH TIME ZONE`
3. Re-run schema DDL on Postgres instance

### License key security
- Generated as UUID v4 (128-bit random) → `secrets.token_urlsafe` equivalent entropy
- Stored only as SHA-256 hash in DB
- Returned plaintext ONCE at generation time
- Desktop app startup validation updates `last_seen_at` (no re-transmission of plaintext)
- `device_id` binding happens on first validation call (optional — user can omit for flexibility)

---

## Tests Added

```
tests/test_auth.py          — 23 tests (6 user CRUD, 6 magic link, 5 session, 4 JWT, 1 require_tier suite=5 tests, 1 rate-limit)
tests/test_subscriptions.py — 17 tests (4 sub repo, 9 license keys, 3 webhook, 3 endpoints)
Total: 40 tests
```

Run the new tests:
```bash
python -m pytest tests/test_auth.py tests/test_subscriptions.py -v
```

---

## Hygiene / Open Items

- [ ] Create the 4 Razorpay plans in dashboard and paste plan IDs into Railway env vars
- [ ] Set `JWT_SECRET` to a production secret (at least 32 random bytes)
- [ ] Configure SMTP or Resend for production email delivery
- [ ] Switch `MOTOQUANT_EMAIL_BACKEND` from `stdout` to `smtp` in Railway env
- [ ] Wrap Next.js layout.js with `<AuthProvider>` to activate auth context site-wide
- [ ] Add `<TierBadge>` and `<UpgradeCTA>` to SimulatorWidget and BuildPage to surface upgrade prompts
- [ ] Apply `require_tier("pro")` to analysis routes when they are added to api.py
- [ ] Apply `require_tier("pro")` to `/api/surrogate/predict` when that route is added (Stream 4)
- [ ] Add Free-tier sim counter enforcement (10 sims/day) — this session added the gating hooks; the counter logic needs to be added to `/api/simulate` and `/api/simulate/quick` routes using a `sim_daily_count` column on `users` or a separate `sim_usage` table
- [ ] Integration-test the Razorpay webhook end-to-end in test mode before going live
- [ ] Delete the orphan Vercel project `motoquant-web` (pre-existing hygiene debt)
