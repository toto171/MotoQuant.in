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
moves**. Before flipping enforcement, do ONE of:

- Add a Render persistent disk (paid plan) mounted at e.g. `/data`, set
  `MOTOQUANT_DB=/data/motoquant.db`, seed once on first boot; or
- Move auth/subscription tables to a managed Postgres (Supabase free tier
  was already the Phase-6 plan of record) and keep the catalog sqlite
  read-only in-image.

## Step 1 — Accounts prerequisite (do this FIRST)

| Env var (Render dashboard) | Value |
|---|---|
| `JWT_SECRET` | 32+ random bytes (`openssl rand -hex 32`). **Required before real users** — the code default is dev-insecure. |
| `SMTP_HOST/PORT/USER/PASS/FROM` *or* `RESEND_API_KEY` | Enables magic-link email delivery. Until set, magic-link runs in dev mode (token echoed in the API response); password login works regardless. |

## Step 2 — Razorpay (India: UPI, cards, netbanking, wallets)

1. Complete KYC at dashboard.razorpay.com.
2. Create 4 subscription **plans** matching the price book in
   `motoquant/payments.py` (`PRICES_INR`):
   Pro ₹499/mo, Pro ₹4,999/yr, Studio ₹1,999/mo, Studio ₹19,990/yr
   (GST collected on top — enable GST in Razorpay settings).
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
