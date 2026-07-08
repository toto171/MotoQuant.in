# Migrate MotoQuant Pro API: Render (free tier) → Oracle Cloud (Always Free)

**Goal:** trade Render's free-tier limits (0.5 shared CPU, 15-min sleep, no
persistent disk) for Oracle's Always Free Ampere A1 shape — 4 dedicated ARM
OCPUs + 24 GB RAM + real persistent block storage, forever free, strictly
better resources than any *paid* tier we looked at. The CPU headroom alone
should fix the multi-minute Build Optimizer runs that Render's 0.5 CPU has
caused since launch.

**Trade-off accepted:** no PaaS dashboard. You manage a real VM — OS
patching, Docker, a reverse proxy for TLS, and (optionally) your own
deploy-on-push wiring. Budget 1-2 hours for the one-time setup below.

**What this migration does NOT need:** no code changes to the physics
engine, no dependency swaps. `requirements-api.txt` is pure Python +
numpy/scipy/fastapi/pydantic/sentry — every one of those ships `manylinux
aarch64` wheels on PyPI, so the existing `Dockerfile` builds and runs
identically on ARM64. Confirmed by inspection before writing this doc; if a
future dependency ever lacks an aarch64 wheel, pip's build-from-source
fallback will still work inside the `python:3.11-slim` image (which is
itself multi-arch) — just slower first build.

**Rollback plan:** keep Render running for 48 hours after Oracle goes live
(same soak-then-suspend pattern used for the Railway → Render move — see
`docs/RENDER_MIGRATION.md`). If anything breaks, revert the one-line
`vercel.json` change back to the Render URL and redeploy Vercel. Total
downtime in the worst case: one Vercel build (~2 min).

---

## Files added in this migration

| File | Purpose |
|---|---|
| `docker-compose.yml` | Runs the existing `Dockerfile`'s API container + a Caddy reverse proxy, on the VM. |
| `Caddyfile` | Reverse proxy config — automatic Let's Encrypt TLS for `api.motoquant.in`. |
| `.env.oracle.example` | Template for VM-local secrets (copy to `.env.oracle` on the VM; gitignored). |
| `.github/workflows/deploy-oracle.yml` | Optional auto-deploy-on-push over SSH. No-ops until you add 3 repo secrets (Step 6). |
| `docs/ORACLE_MIGRATION.md` | This file. |

Files **not** modified yet (deliberately — see Step 5): `vercel.json`,
`web/next.config.js`, `scripts/session_postflight.sh`,
`.github/workflows/keepalive.yml`, `motoquant/keepwarm.py`,
`web/app/api/wake/route.js`. These all hardcode the Render URL or exist
purely to work around Render's sleep behavior. They get updated/retired in
Step 5, **after** you have a live, health-checked Oracle endpoint to point
at — flipping them before that exists would take production down for no
reason.

---

## Step 1 — Create the Always Free Ampere A1 instance

This part only you can do — it needs your Oracle account and console access.

1. Sign up at https://signup.oraclecloud.com if you don't already have a
   tenancy. **Pick your home region carefully at signup** — Always Free
   resource availability is scoped to your home region and can't be changed
   later without a new tenancy. `ap-mumbai-1` or `ap-hyderabad-1` are the
   closest to Indian users (better than Render's Singapore region) and
   both offer the Ampere A1 Always Free shape.
2. **Compute → Instances → Create instance.**
3. **Image:** Canonical Ubuntu 22.04 (aarch64/ARM build — the console
   defaults to the right architecture once you pick the shape below first).
4. **Shape:** click Change shape → **Ampere → VM.Standard.A1.Flex** → set
   **4 OCPUs / 24 GB memory** (the full Always Free Ampere allowance; using
   less doesn't save you anything since it's free either way).
5. **Networking:** use the default VCN or create one; **assign a public
   IPv4 address** (checkbox is on by default).
6. **SSH keys:** let the console generate a keypair and download the
   private key, or paste your own public key. You'll need this to SSH in.
7. Click **Create**.

**Known gotcha — "Out of capacity for shape VM.Standard.A1.Flex":** Always
Free Ampere is popular and demand-limited per availability domain. If you
hit this error:
- Retry a few times over the next hour (capacity frees up as other
  tenancies' instances get reclaimed/resized).
- Try a different Availability Domain in the same region (the create form
  has an AD selector).
- If truly stuck, provision with fewer OCPUs first (e.g. 2 OCPU/12 GB) to
  get *something* running, then resize up later via **Edit → Shape
  configuration** once capacity opens — resizing is a stop/start, not a
  rebuild, and doesn't lose the disk.

---

## Step 2 — First-boot VM setup

SSH in with the key from Step 1 (Ubuntu images use the `ubuntu` user):

```bash
ssh -i /path/to/your/private_key ubuntu@<vm-public-ip>
```

Install Docker + the Compose plugin (Ubuntu 22.04, ARM64 — Docker's repo
serves `arm64` packages natively):

```bash
sudo apt-get update && sudo apt-get upgrade -y
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker "$USER"
# log out and back in so the group membership takes effect
exit
```

```bash
ssh -i /path/to/your/private_key ubuntu@<vm-public-ip>
docker --version && docker compose version   # sanity check
```

Clone the repo (deploy path assumed by `docker-compose.yml` and the
optional GH Actions workflow is `/opt/motoquant`):

```bash
sudo mkdir -p /opt/motoquant && sudo chown "$USER:$USER" /opt/motoquant
git clone https://github.com/da25mem5s02-debug/MotoQuant_v1.git /opt/motoquant
cd /opt/motoquant
```

---

## Step 3 — Open the firewall (two layers, both required)

Oracle Cloud has **two independent firewalls** in front of the VM, and
missing either one silently breaks TLS cert issuance with no obvious error:

**(a) OCI Security List / Network Security Group** (console-side): your
VM's VCN → **Security Lists** → default security list → **Add Ingress
Rules**:
- Source CIDR `0.0.0.0/0`, TCP, destination port `80`
- Source CIDR `0.0.0.0/0`, TCP, destination port `443`
- Port `22` (SSH) should already be open from instance creation.

**(b) The VM's own iptables** — Oracle's stock Ubuntu image ships with
`iptables` rules that block inbound traffic beyond SSH *even though the
console-side security list allows it*. This is the single most common
"why won't my cert issue" gotcha on OCI. Fix on the VM:

```bash
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save
```

(`-I INPUT 6` inserts before the default REJECT rule that ships near the
top of the chain — check `sudo iptables -L INPUT -n --line-numbers` if your
image's rule order differs.)

---

## Step 4 — Point DNS, deploy, verify

1. In your DNS provider (wherever `motoquant.in` is managed), add an **A
   record**: `api.motoquant.in` → `<vm-public-ip>`. Propagation is usually
   under 10 minutes.
2. On the VM:

```bash
cd /opt/motoquant
cp .env.oracle.example .env.oracle
# edit .env.oracle if you want chat/auth/payments secrets active now —
# all optional, the simulator works without any of them
docker compose up -d --build
```

First build takes a few minutes (same Dockerfile, cold pip cache). Watch
it come up:

```bash
docker compose logs -f api
```

3. **Test the API container directly first** (bypasses Caddy/DNS/TLS —
   isolates whether the app itself is healthy):

```bash
curl http://<vm-public-ip>:8000/api/health
# expect: {"status":"ok","database":"connected","bike_count":...}
```

   Note: port 8000 isn't opened in Step 3's firewall rules on purpose (only
   80/443 are public) — from your own machine this will only work if you
   SSH-tunnel it (`ssh -L 8000:localhost:8000 ubuntu@<vm-ip>`) or curl it
   from *inside* the VM. Either is fine for this smoke test.

4. **Test through Caddy + TLS** once DNS has propagated:

```bash
curl https://api.motoquant.in/api/health
curl "https://api.motoquant.in/api/bikes?limit=3"
curl -X POST https://api.motoquant.in/api/simulate/quick \
  -H "Content-Type: application/json" \
  -d '{"bike_id": 1, "rider_mass_kg": 80}'
```

If the TLS handshake hangs or fails, it's almost always Step 3(b) (the
VM-local iptables rules) — Caddy logs (`docker compose logs caddy`) will
show ACME challenge failures if Let's Encrypt can't reach port 80.

---

## Step 5 — Soft cutover (only after Step 4 is fully green)

Five small, mechanical edits — happy to make these the moment you confirm
`https://api.motoquant.in/api/health` is live:

1. **`vercel.json`** — `destination` in the `/api/:path*` rewrite:
   `https://motoquant-api.onrender.com/api/:path*` → `https://api.motoquant.in/api/:path*`
2. **`web/next.config.js`** — same URL swap in the `backend` fallback.
3. **`scripts/session_postflight.sh`** — `RENDER_HEALTH` constant → the new
   URL (keeps the deploy-verify postflight check meaningful).
4. **Retire the Render-sleep workarounds** — a real always-on VM never
   sleeps, so these three become dead weight:
   - `.github/workflows/keepalive.yml` — delete or disable the `schedule:`
     trigger.
   - `motoquant/keepwarm.py` + its startup-hook call in `motoquant/api.py`
     — the loop already no-ops without `RENDER_EXTERNAL_URL` (which Oracle
     never sets), so it's safe to leave inert, but cleanest to remove once
     confirmed unnecessary.
   - `web/app/api/wake/route.js` + the three `crons` entries in
     `vercel.json` — same reasoning.
5. Commit + push. Vercel auto-redeploys in ~90s. Then:

```bash
curl https://www.motoquant.in/api/health
# now routes through Oracle instead of Render
```

Walk through the live simulator widget on `motoquant.in` and confirm a
`/api/simulate/quick` call comes back well under 200ms (no cold-start tax
at all now — this was the whole point).

---

## Step 6 — Optional: wire up auto-deploy-on-push

Render auto-deployed on every push; `.github/workflows/deploy-oracle.yml`
(already added) reproduces that over plain SSH once three repo secrets
exist:

1. Generate a deploy-only SSH keypair (don't reuse your personal key):
   ```bash
   ssh-keygen -t ed25519 -f oracle_deploy_key -N "" -C "motoquant-deploy"
   ```
2. On the VM, append the **public** half to the deploy user's authorized
   keys: `cat oracle_deploy_key.pub >> ~/.ssh/authorized_keys`
3. In GitHub: **Settings → Secrets and variables → Actions → New repository
   secret**, add:
   - `ORACLE_SSH_HOST` = `api.motoquant.in` (or the VM's public IP)
   - `ORACLE_SSH_USER` = `ubuntu`
   - `ORACLE_SSH_KEY` = contents of the **private** half (`oracle_deploy_key`)
4. Delete the local copies of both key files once uploaded.

The workflow only fires on pushes touching backend-relevant paths (mirrors
`render.yaml`'s old `buildFilter` list) and no-ops with a clear warning if
the secrets aren't set yet.

---

## Step 7 — 48-hour soak, then suspend Render

Same discipline as the Railway → Render cutover:

1. For 48 hours, leave Render running (same Dockerfile, same DB) as an
   instant-flip fallback.
2. Monitor: Oracle VM (`docker compose logs -f`, `htop` for actual CPU
   headroom vs Render's 0.5-core ceiling), GitHub Actions (if Step 6 is
   wired up), the live simulator widget.
3. After 48 clean hours: Render dashboard → `motoquant-api` → **Settings →
   Suspend** (don't delete yet — recoverable fallback for 30 more days).
4. Update `CLAUDE.md`'s dated session entry: strike the Render-tier notes,
   add "Migrated to Oracle Cloud Always Free — see
   `docs/ORACLE_MIGRATION.md`."

After 30 more days, if Oracle has been solid, delete the Render service and
`render.yaml` (or keep `render.yaml` in the repo purely as a documented
fallback path — your call).

---

## Rollback (if Oracle breaks within the soak window)

1. Revert the `vercel.json` / `next.config.js` edits from Step 5 back to
   the Render URL.
2. Commit + push. Vercel redeploys in ~90s.
3. `motoquant.in` is back on Render.
4. Debug the Oracle VM at your own pace — nothing time-pressured since
   Render is serving traffic again.

---

## What changes vs Render free tier

| Property | Render Free | Oracle Always Free |
|---|---|---|
| CPU | 0.5 shared vCPU | 4 dedicated ARM OCPUs |
| RAM | 512 MB | 24 GB |
| Sleep / cold start | sleeps after 15 min idle, ~30-60s wake | never sleeps — it's your VM |
| Persistent disk | none on free tier (baked image only) | real block storage, always persistent |
| TLS | managed automatically | Caddy + Let's Encrypt (self-managed, automatic renewal) |
| Deploy | git-push auto-deploy | manual `docker compose up -d --build`, or optional SSH-based auto-deploy (Step 6) |
| OS patching | Render's problem | yours (`apt-get upgrade` periodically) |
| Cost | $0/mo | $0/mo forever (Always Free, not a trial) |

The CPU/RAM upgrade should directly fix the documented Build
Optimizer/Autotune slowness (multi-minute runs on Render's 0.5 CPU) —
worth re-running a timing comparison once cut over, since it may make the
surrogate-model fallback path less load-bearing for interactive UX (the
surrogate itself stays — it's still the right default for slider-driven
previews — but the "full sim over a full VM core" ceiling moves way up).
