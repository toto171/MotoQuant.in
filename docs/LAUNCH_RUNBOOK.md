# Launch Runbook — Go-Live Morning Checklist

> Written 2026-08-21 (commercialization launch prep). **This is the operator's
> execution doc for launch morning**: one ordered, copy-pasteable checklist.
> Timeline: credentials (Razorpay / JWT / Resend) gathered the day before,
> billing flipped on Monday. Background and rationale live in
> `docs/COMMERCIAL_LAUNCH.md` (what must be true) and `docs/PAYMENTS_SETUP.md`
> (per-provider mechanics); this doc is the ORDER and the exact commands.
>
> Everything here is dashboard/env work — **zero code changes on launch day.**
> Steps 0–5 are safe to do while the site stays in open beta. Step 6 is the
> only user-visible switch.

Base URLs used throughout:

- API (Render, direct): `https://motoquant-api.onrender.com`
- Site (Vercel): `https://motoquant.in` (proxies `/api/*` to Render)

---

## Step 0 — Render plan upgrade + persistent disk (PREREQ, do first)

Without this, **every deploy wipes accounts, saved runs and subscriptions**.
Nothing else in this runbook is worth doing until the disk exists.

The durability flip is THREE edits in **ONE commit / ONE deploy**, all in
`render.yaml` (the edits are already written there as commented diffs):

1. `plan: free` → `plan: starter`
2. Uncomment the `disk:` block at the bottom of the file:
   `name: motoquant-data`, `mountPath: /data`, `sizeGB: 1`
3. Repoint `MOTOQUANT_DB` from `/app/motoquant.db` to `/data/motoquant.db`

**Do NOT split these across deploys.** A blueprint re-apply with the disk
block enabled while the plan is still `free` FAILS — Render disks require a
paid plan.

Push, then watch the **first-boot logs** in the Render dashboard for the
entrypoint seed line (from `docker-entrypoint.sh`):

```
[entrypoint] persistent DB /data/motoquant.db not found — seeding from image copy /app/motoquant.db
```

(Subsequent boots print `persistent DB /data/motoquant.db present — keeping
existing user data (no overwrite)` instead.)

**If the service crash-loops at this point:** the container runs as the
unprivileged user `app` (Dockerfile `USER app`), so a root-owned `/data`
mount makes the seed `cp` fail and the entrypoint (`set -e`) exits. Mount
ownership is Render's to provide — if the seed line never appears and the
logs show a permission error on `/data`, raise it with Render support before
proceeding.

Verify durability end-to-end:

```bash
curl -s https://motoquant-api.onrender.com/api/health
# expect: {"status":"ok","database":"connected","bike_count":541}
```

Then register a throwaway account on `https://motoquant.in/login?signup=1`,
trigger a redeploy (Render dashboard → Manual Deploy, or push any backend
commit), and confirm the account still signs in afterwards. **The throwaway
surviving a deploy is the pass condition for Step 0.**

Starter has no sleep behavior, so cold starts stop being a thing (see
Step 8 re: the keep-alive cron).

---

## Step 1 — Environment variables (Render dashboard → motoquant-api → Environment)

**ORDER IS LOAD-BEARING.** Set `JWT_SECRET` FIRST — the API **refuses to
boot** (`RuntimeError` from the `auth.py` boot guard) if the JWT secret is
still the public default while `MOTOQUANT_BILLING_ENFORCE=true`. Setting it
last means the flip in Step 6 takes the site down instead of turning
billing on.

| # | Env var | Value | Why | When |
|---|---------|-------|-----|------|
| 1 | `JWT_SECRET` | 32+ random bytes — generate with `openssl rand -hex 32` | Session-token signing key. The code default is public; with it, anyone can forge access tokens and self-upgrade. Boot guard hard-fails on the default once billing is enforced. | **BEFORE anything else** (it restarts the service; do it while still in beta) |
| 2 | `MOTOQUANT_BASE_URL` | `https://motoquant.in` | Checkout callbacks, magic links, 402 upgrade URLs are all built from this. | Already in `render.yaml` — just confirm it is present and unchanged |
| 3 | `RESEND_API_KEY` | Resend dashboard → API Keys | Magic-link sign-in email. **VERIFY the sending domain in the Resend dashboard first — all DNS records green — or every send returns 403.** | With the email domain verified, before launch |
| 4 | `SMTP_FROM` | e.g. `MotoQuant <signin@motoquant.in>` | From address for magic-link mail (used by both Resend and SMTP transports). | Together with #3 |
| 5 | `RAZORPAY_KEY_ID` | Razorpay dashboard → API Keys | Checkout + API auth. | After Step 2 KYC/plans |
| 6 | `RAZORPAY_KEY_SECRET` | same place | " | " |
| 7 | `RAZORPAY_WEBHOOK_SECRET` | the secret you type into the webhook form in Step 2 | Webhook signature verification — fails closed when unset. | With Step 2 webhook |
| 8 | `PLAN_ID_PRO_MONTHLY` | `plan_…` id from Step 2 | Maps Razorpay plans → tiers. An unknown/unset plan id makes webhook tier grants unresolvable (logged, redelivered — see Step 7). | After creating the 4 plans |
| 9 | `PLAN_ID_PRO_YEARLY` | `plan_…` | " | " |
| 10 | `PLAN_ID_STUDIO_MONTHLY` | `plan_…` | " | " |
| 11 | `PLAN_ID_STUDIO_YEARLY` | `plan_…` | " | " |
| 12 | `STRIPE_SECRET_KEY` *(optional)* | `sk_live_…` | International cards. Skippable at launch — Razorpay alone serves the Indian market. | Step 3, if doing Stripe |
| 13 | `STRIPE_WEBHOOK_SECRET` *(optional)* | `whsec_…` | Stripe webhook signatures — always set it if Stripe is live. | " |
| 14 | `STRIPE_PRICE_PRO_MONTHLY` / `STRIPE_PRICE_PRO_YEARLY` / `STRIPE_PRICE_STUDIO_MONTHLY` / `STRIPE_PRICE_STUDIO_YEARLY` *(optional)* | `price_…` ids | Maps Stripe prices → tiers. | " |
| 15 | `MOTOQUANT_BACKUP_ENABLE` | `true` | Turns on the **in-app daily backup scheduler** (new 2026-08-21, `motoquant/backup.py`): the web service itself takes a hot, integrity-verified, gzipped snapshot every 24 h (`MOTOQUANT_BACKUP_INTERVAL_H` to change). **No separate Render Cron Job needed.** | Once the disk exists (Step 0) — pointless before |
| 16 | `MOTOQUANT_BACKUP_DIR` | `/data/backups` | Snapshots must live on the persistent disk, not the ephemeral container FS. | With #15 |
| 17 | `MOTOQUANT_BACKUP_UPLOAD_CMD` | e.g. `rclone copy {path} r2:motoquant-backups/` | On-disk snapshots protect against a bad migration, **not** against losing the disk — this copies each snapshot off-box (`{path}` is substituted). | With #15, once an rclone remote (R2/S3/Drive) exists |

Do **NOT** set `MOTOQUANT_BILLING_ENFORCE` yet — that is Step 6.

---

## Step 2 — Razorpay: plans + webhook

1. KYC complete at dashboard.razorpay.com (unregistered sole proprietorship,
   personal PAN — already the account's registered state).
2. **GST must stay OFF** — on the account AND on every plan. No GSTIN exists
   (below the ₹20 lakh services threshold) so GST cannot legally be
   collected, and the site promises no GST is charged. The plan amounts
   below are the total payable.
3. Create exactly 4 subscription plans (Subscriptions → Plans → Create).
   **Razorpay takes amounts in paise:**

   | Plan | Amount (₹) | Amount (paise) | Interval |
   |---|---|---|---|
   | Pro Monthly | ₹499 | `49900` | monthly |
   | Pro Yearly | ₹4,999 | `499900` | yearly |
   | Studio Monthly | ₹1,999 | `199900` | monthly |
   | Studio Yearly | ₹19,990 | `1999000` | yearly |

   Copy each resulting `plan_…` id into the matching `PLAN_ID_*` env var
   (Step 1 rows 8–11).
4. Add the webhook (Settings → Webhooks → Add New Webhook):
   - URL: `https://motoquant-api.onrender.com/api/subscriptions/webhook`
   - Events: `subscription.activated`, `subscription.charged`,
     `subscription.halted`, `subscription.cancelled`,
     `subscription.completed`, `subscription.paused`,
     `subscription.authenticated`
   - Type a strong secret into the form and set the **same value** as
     `RAZORPAY_WEBHOOK_SECRET` (Step 1 row 7). The endpoint fails closed —
     with the env var unset, every delivery is rejected.

---

## Step 3 — Stripe (optional, international cards)

Skippable on launch morning; Razorpay covers the home market. If doing it:

1. Create one product per tier with recurring prices (USD anchors:
   Pro $5.99/mo · $59/yr, Studio $23.99/mo · $239/yr), copy the `price_…`
   ids into the `STRIPE_PRICE_*` env vars.
2. Add the webhook endpoint:
   - URL: `https://motoquant-api.onrender.com/api/payments/webhook/stripe`
   - Events: `checkout.session.completed`, `customer.subscription.updated`,
     `customer.subscription.deleted`, `invoice.payment_failed`
   - Set the signing secret as `STRIPE_WEBHOOK_SECRET`.

---

## Step 4 — Website KYC block (Razorpay website review cross-checks this)

Fill the `BUSINESS` constant at the top of `web/app/contact/page.js`:

- `legalName` — the legal name on the PAN the Razorpay account settles to
- `addressLines` — registered/operating address, one array entry per line
- `phone` — the phone number on the KYC record

Use **EXACTLY the values registered on the Razorpay KYC record** — the
activation review cross-checks the website against it; a mismatch fails
review and reads as fraud. Fields left `null` simply don't render, so a
missing value is recoverable, a wrong one is not.

Commit + push. The `web-verify` CI gate runs `next build`, and Vercel
auto-deploys the page (~2 min). Confirm at `https://motoquant.in/contact`.

---

## Step 5 — Test-mode purchase (REQUIRED before the flip)

Switch the Razorpay dashboard to **Test Mode**, generate test-mode API keys
and a test-mode webhook (same URL + events as Step 2), and temporarily point
the `RAZORPAY_*` env vars at them. Test Mode has its own plan namespace —
recreate the 4 plans there (same paise amounts) and point the `PLAN_ID_*`
env vars at the test-mode plan ids for the duration of this step. Then:

```bash
API=https://motoquant-api.onrender.com

# 1) Throwaway account (returns access_token in the JSON)
curl -s -X POST $API/api/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"launch-test-1@example.com","password":"a-long-test-password"}'

# export the token from the response:
export TOKEN="<access_token from above>"

# 2) Pro monthly checkout — response carries checkout_url (Razorpay short_url)
curl -s -X POST $API/api/payments/checkout \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"tier":"pro","billing_cycle":"monthly","provider":"razorpay"}'

# 3) Open checkout_url in a browser, pay with a Razorpay TEST card/UPI.

# 4) Watch Render logs for the subscription.activated webhook arriving,
#    then confirm the tier landed:
curl -s $API/api/subscriptions/status -H "Authorization: Bearer $TOKEN"
# expect: {"tier":"pro","subscription_status":"active", ...}

# 5) Cancel — from the account page (https://motoquant.in/account), or:
curl -s -X POST $API/api/subscriptions/cancel -H "Authorization: Bearer $TOKEN"

# 6) Status reflects the cancellation:
curl -s $API/api/subscriptions/status -H "Authorization: Bearer $TOKEN"
# expect: subscription_status "cancelled" (immediate for a never-captured
# mandate) or an active-until-period-end state with cancel scheduled
```

If any step misbehaves, fix it NOW — this is the exact flow real customers
hit. When green, switch the dashboard back to **Live Mode** and restore the
live values for `RAZORPAY_*` (keys + webhook secret) AND the four
`PLAN_ID_*` vars.

---

## Step 6 — THE FLIP

Set in the Render dashboard (triggers a service restart, ~1 min):

```
MOTOQUANT_BILLING_ENFORCE=true
```

If the service does not come back: the near-certain cause is `JWT_SECRET`
missing/default (Step 1 row 1) — the boot guard refuses to start. Fix the
env var; if needed, flip enforcement back to `false` to get the site up
while you do.

Post-flip verification (run all four):

```bash
API=https://motoquant-api.onrender.com

# (a) Anonymous free-tier quota: 30 full sims/day; the 31st is 402. (curl
#     meters per IP because it sends no X-MQ-Client-Id header — browser
#     clients meter per client id, which is the point for CGNAT users.)
#     The `sleep 3` matters — /api/simulate also carries a 30-req/60s per-IP
#     rate fuse, and a tight loop hits that (429) before the daily quota:
for i in $(seq 1 31); do
  curl -s -o /dev/null -w "sim $i -> %{http_code}\n" \
    -X POST $API/api/simulate \
    -H 'Content-Type: application/json' -d '{"bike_id": 1}'
  sleep 3
done
# expect: sims 1-30 -> 200 (X-Sims-Remaining counts down),
#         sim 31 -> 402 (body: "error":"quota_exceeded"). ~3-4 min total —
#         each sim is a full RK4 run (1-3s on the Starter CPU) on top of the
#         sleeps; don't abort early thinking it hung.

# (b) Pro-gated route, unauthenticated -> 401
curl -s -o /dev/null -w "%{http_code}\n" -X POST $API/api/optimize/build \
  -H 'Content-Type: application/json' -d '{"bike_id":1,"budget_inr":100000}'
# expect: 401

# (c) Save-run with a FREE-tier token -> 402 upgrade_required
#     (register a fresh throwaway as in Step 5.1, export TOKEN, then:)
curl -s -X POST $API/api/simulate/save \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"bike_id":1,"et_quarter_s":9.93,"trap_speed_kmh":230}'
# expect: 402, body contains "error":"upgrade_required"

# (d) Pricing page flips to paid WITHOUT a web deploy — the CTAs read this:
curl -s $API/api/payments/config
# expect: "beta": false, razorpay configured: true
```

Then eyeball `https://motoquant.in/pricing` in a browser: the "Free during
beta" ribbon is gone and the CTAs are real checkout buttons.

---

## Step 7 — Rollback + week-one watch

**Rollback is an env change only, no deploy:** set
`MOTOQUANT_BILLING_ENFORCE=false` in the Render dashboard. Every tier gate
reopens instantly; the pricing page reverts to beta CTAs on its next
`/api/payments/config` read. **Webhooks keep applying tier changes in either
mode**, so anyone who paid during the enforced window keeps their tier and
nothing desyncs while enforcement is off.

**Week one:** watch the Render logs for `log.error` lines from the webhook
handlers — specifically **unknown plan ids** (tier unresolvable from
`plan_id` → a `PLAN_ID_*` env var is mistyped or missing) and
**unresolvable webhook users** ("cannot resolve user"). Those are the
operator signal that env/plan config is wrong. Both are answered non-2xx on
purpose, so **the provider redelivers the event automatically once the env
is fixed** — no tier grant is permanently lost.

---

## Step 8 — After launch (NOT blocking)

- **Keep-alive cron:** `.github/workflows/keepalive.yml` has had its
  schedule paused since 2026-07-14 (Actions-minutes cap). Starter instances
  do not sleep, so the cron is now moot — leave it paused (it still doubles
  as a manual uptime probe via `workflow_dispatch`).
- **Client-side main sims:** trigger the `pyodide-parity.yml` workflow from
  the GitHub Actions tab when ready — it is the go/no-go proof for wiring
  Pyodide main sims into the UI (see `docs/CLIENT_COMPUTE.md`).
- **PR housekeeping:** #117 is merge-worthy; #88 verify + close; #102
  rebase. 15 fully-merged remote branches are deletable.
- **848-EVO catalog rename migration** rides a separate post-launch PR.
