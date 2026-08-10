# Payments Go-Live Runbook (Razorpay + Stripe)

> Written June 7, 2026 alongside the unified payments layer
> (`motoquant/payments.py`). Everything below is an env-var exercise —
> **zero code changes** are needed to start charging money.

## Current state (open beta)

- `MOTOQUANT_BILLING_ENFORCE=false` (render.yaml): every tier gate passes,
  signed-in users are attached for attribution, anonymous users pass with `{}`.
- `/api/payments/config` advertises `beta: true` → the pricing page shows
  "Free during beta" CTAs and never calls checkout.
- No payment provider is configured → `POST /api/payments/checkout` returns a
  friendly 503.

## Step 0 — Durable storage (HARD BLOCKER for paid launch)

`motoquant.db` is baked into the Docker image and Render free tier has no
persistent disk → **user accounts, saved runs and subscription rows are
wiped on every deploy** (and every push auto-deploys). Acceptable during
the free beta (accounts are convenience only); **unacceptable once money
moves**.

**The mechanism is now shipped** (June 2026): `docker-entrypoint.sh` seeds a
persistent-disk DB from the baked image copy on first boot, then preserves it
across all later deploys. On the free tier it is a verified no-op (seed path ==
target path). To turn durability on, do ONE of:

**Option A — Render persistent disk (recommended, ~$1/mo + paid instance).**
Render disks require a paid plan (Starter+). Then it's a 2-step flip in
`render.yaml` (both changes are already written as commented diffs in that file):
1. Uncomment the `disk:` block (`name: motoquant-data`, `mountPath: /data`, `sizeGB: 1`).
2. Change `MOTOQUANT_DB` from `/app/motoquant.db` to `/data/motoquant.db`.
Push → first boot copies the seeded catalog to `/data`, and every deploy
thereafter keeps the accumulated users/runs/subscriptions. Verify with
`/api/health` (`bike_count` stays 501) and by registering a test account,
deploying, and confirming the account survives.

**Option B — managed Postgres for auth/subscription tables (Supabase free
tier, the Phase-6 plan of record).** Keep the catalog sqlite read-only
in-image; move only the durable tables. Larger change (repo layer +
connection routing); revisit if disk cost or sqlite write-concurrency on a
shared instance becomes the constraint.

## Step 1 — Accounts prerequisite (do this FIRST)

| Env var (Render dashboard) | Value |
|---|---|
| `JWT_SECRET` | 32+ random bytes (`openssl rand -hex 32`). **Required before real users** — the code default is dev-insecure, and the server now refuses to boot with it once billing is enforced. |
| `RESEND_API_KEY` + `SMTP_FROM` *(recommended)* | Enables magic-link email. Resend's free tier covers launch volume and needs no SMTP server — but the sending domain must be verified in the Resend dashboard first, or the API returns 403. |
| *or* `SMTP_HOST/PORT/USER/PASS/FROM` | Same thing over plain SMTP. |

The transport is **derived from whichever of those you set** — there is no
separate enable flag. Precedence: `MOTOQUANT_EMAIL_BACKEND` (explicit
override) → Resend → SMTP → stdout. Set `SMTP_FROM` in both cases; it is the
From address for either transport.

> **Fixed 2026-08-10 — this used to be a trap.** `MOTOQUANT_EMAIL_BACKEND`
> defaulted to `stdout` and the send guard short-circuited on it, so following
> the SMTP row above *exactly* still sent zero email while the API answered
> "Sign-in link sent. Check your inbox." Resend was named here and in
> `auth.py`'s docstring but had **no implementation at all**. Both are now
> real, and a deployed host with no transport configured returns 503 from
> `/api/auth/magic-link` instead of falsely reporting success (it also warns
> at boot). Password sign-in was, and remains, unaffected.

## Step 1b — Backups (do this WITH the disk, not after)

`scripts/backup_db.py` takes a hot, integrity-checked, gzipped snapshot using
the SQLite online-backup API (safe against concurrent writers — verified
against a WAL database taking ~1,300 commits mid-backup) and prunes to the
newest N. 18 MB DB → ~3 MB snapshot.

```bash
python scripts/backup_db.py --db /data/motoquant.db --keep 14
```

Snapshots default to `<db-dir>/backups`. That protects against a bad
migration or an errant DELETE, but **not** against losing the disk — set
`MOTOQUANT_BACKUP_UPLOAD_CMD` to copy each one off-box (`{path}` is
substituted):

```
MOTOQUANT_BACKUP_UPLOAD_CMD='rclone copy {path} r2:motoquant-backups/'
```

Exit codes: `0` ok · `1` backup failed · `2` snapshot good but upload failed.
Schedule it as a Render Cron Job (daily) once you are on a paid plan.

## Step 2 — Razorpay (India: UPI, cards, netbanking, wallets)

1. Complete KYC at dashboard.razorpay.com.
2. Create 4 subscription **plans** matching the price book in
   `motoquant/payments.py` (`PRICES_INR`):
   Pro ₹499/mo, Pro ₹4,999/yr, Studio ₹1,999/mo, Studio ₹19,990/yr.

   **Do NOT enable GST in Razorpay settings.** MotoQuant currently operates as
   an unregistered sole proprietorship below the ₹20 lakh turnover threshold
   for services, so it has no GSTIN and cannot legally collect GST. The plan
   amounts above are the total payable. Site copy (terms, pricing, refunds,
   `/api/payments/config`) states this explicitly as of 2026-08-10 — it
   previously promised "18% GST added at checkout" and a provider-issued tax
   invoice, neither of which was deliverable.

   On crossing ₹20 lakh: register for a GSTIN within 30 days, then charge 18%
   on software services from that date forward. That is a coordinated change —
   Razorpay GST settings, `PRICES_INR`, `gst_note` in `payments.py`, and the
   GST wording in `/terms` §3, `/refunds` §7 and `/pricing` all move together.
3. Set env vars: `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`,
   `PLAN_ID_PRO_MONTHLY`, `PLAN_ID_PRO_YEARLY`,
   `PLAN_ID_STUDIO_MONTHLY`, `PLAN_ID_STUDIO_YEARLY`.
4. Add webhook: `https://motoquant-api.onrender.com/api/subscriptions/webhook`
   — events: `subscription.activated/charged/halted/cancelled/completed/paused`.
   Set the webhook secret as `RAZORPAY_WEBHOOK_SECRET`.

## Step 3 — Stripe (international cards)

1. Activate the Stripe account (stripe.com).
2. Create one product per tier with recurring **prices** (suggested USD
   anchors live in `PRICES_USD_DISPLAY`: Pro $5.99/mo · $59/yr, Studio
   $23.99/mo · $239/yr).
3. Set env vars: `STRIPE_SECRET_KEY`, `STRIPE_PRICE_PRO_MONTHLY`,
   `STRIPE_PRICE_PRO_YEARLY`, `STRIPE_PRICE_STUDIO_MONTHLY`,
   `STRIPE_PRICE_STUDIO_YEARLY`.
4. Add webhook endpoint:
   `https://motoquant-api.onrender.com/api/payments/webhook/stripe`
   — events: `checkout.session.completed`,
   `customer.subscription.updated`, `customer.subscription.deleted`,
   `invoice.payment_failed`. Set the signing secret as
   `STRIPE_WEBHOOK_SECRET` (signatures are enforced when set; **always set
   it in prod**).

No Stripe SDK is installed — calls go through stdlib `urllib`, webhook
signatures through stdlib `hmac` (`t=`/`v1=` scheme, 300 s tolerance).
Duplicate webhook deliveries are dropped via the `payment_events`
(provider, event_id) ledger.

## Step 4 — Flip the switch

Set `MOTOQUANT_BILLING_ENFORCE=true` in the Render dashboard (or
render.yaml). Effects, immediately and with no deploy:

- `require_tier("pro"|"studio")` starts returning 401 (anonymous) /
  402 `upgrade_required` (insufficient tier) on gated routes.
- `/api/payments/config` flips `beta: false` → pricing-page CTAs become
  real checkout buttons (Razorpay first, Stripe fallback, per-user choice
  via `provider` field).

Smoke-test in Razorpay/Stripe **test mode** first: register a fresh user →
checkout → pay with a test card/UPI → confirm the webhook upgrades
`users.tier` → `/api/auth/me` shows the new tier → license-key generation
works on the account page.

## PayPal (planned)

`POST /api/payments/checkout {provider: "paypal"}` and
`/api/payments/webhook/paypal` are stubbed (503/501). Implementation slot:
add a `_create_paypal_checkout` mirroring the Stripe pattern (OAuth2
client-credentials + Orders v2 API) once a business account exists.
`PAYPAL_CLIENT_ID` / `PAYPAL_CLIENT_SECRET` env names are already reserved.
