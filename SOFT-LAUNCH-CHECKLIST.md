# Soft Launch Checklist — motoquant.in Live

## ✅ Done
- [x] Landing page React component created (`landing-page.jsx`)
- [x] Deployment guide (`DEPLOYMENT.md`) with step-by-step instructions
- [x] Physics validation benchmarks highlighted (K5, R1, Hayabusa)
- [x] GitHub and CTA links configured

## 📋 To Do (In Order)

### Phase 3A: GitHub Repository (30 min)
- [ ] Create GitHub repo: `https://github.com/YOUR_USERNAME/motoquant`
- [ ] Push existing motoquant code to main branch
- [ ] Verify README exists and describes the project
- [ ] Update GitHub About: "Physics engine for drag racing"

### Phase 3B: Vercel Setup (1 hour)
- [ ] Create `pages/_app.jsx` and copy landing page logic
- [ ] Create `next.config.js`, `tailwind.config.js`, `postcss.config.js`
- [ ] Create/update `package.json` with dependencies
- [ ] Run `npm install && npm run build` locally to test
- [ ] Push all config files to GitHub
- [ ] Sign in to Vercel (vercel.com) with GitHub account
- [ ] Import `motoquant` repo into Vercel
- [ ] Verify build succeeds and preview URL works

### Phase 3C: Domain Setup (1 hour, but DNS is slow)
- [ ] Go to Vercel project → Settings → Domains
- [ ] Add domain: `motoquant.in`
- [ ] Copy Vercel nameservers
- [ ] Log into domain registrar (Hostinger, etc.)
- [ ] Update DNS: replace nameservers with Vercel's
- [ ] Wait 24–48 hours for propagation (check status in Vercel)
- [ ] Test: visit motoquant.in in browser

### Phase 3D: Announce & Gather Feedback (Ongoing)
- [ ] Tweet/share the live URL
- [ ] Post in Indian drag racing communities
- [ ] Monitor GitHub issues for bike/feature requests
- [ ] Document feedback for Phase 3 (calibration pipeline)

---

## Effort Estimate
- **Setup:** 2–3 hours (mostly waiting for DNS)
- **Live by:** 24–48 hours (DNS propagation)
- **Ongoing:** Monitor GitHub + Phase 2 continuation

---

## Success Criteria
- ✓ motoquant.in loads and displays landing page
- ✓ Navigation links work (GitHub, quickstart)
- ✓ Responsive on mobile, tablet, desktop
- ✓ GitHub links point to public repo
- ✓ Validation benchmarks are visible and compelling

---

## Phase 2 Continuation (While DNS Propagates)

Don't wait for DNS to finish—work on Phase 2 remaining in parallel:

```bash
# Bulk scrape Japanese Big 4 (Honda, Yamaha, Suzuki, Kawasaki)
python -m motoquant.run scrape --bulk --priority 1

# Expand known_bikes.py with ~30 hand-curated Indian-market bikes
# See CLAUDE.md for target list

# Add international venues (Santa Pod, Pomona, Gainesville, Sydney)
python -m motoquant.run db stats  # Check current venue count
```

This way, when Phase 3 (calibration pipeline) starts, you'll have a rich bike library ready.

---

## Questions Before You Start?

- Do you have a GitHub account? (If not, create at github.com — free)
- Where did you buy motoquant.in? (Need registrar login to update DNS)
- Do you want the repo public or private initially? (Recommend public for open source)

Once you confirm, you're ready to proceed with Phase 3A above.
