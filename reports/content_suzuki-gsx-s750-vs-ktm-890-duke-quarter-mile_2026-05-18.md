# Content Report — suzuki-gsx-s750-vs-ktm-890-duke-quarter-mile
## Date: 2026-05-18

### Target keyword
Primary: `suzuki gsx-s750 quarter mile`
Secondary: `ktm 890 duke quarter mile`, `gsx-s750 vs 890 duke drag race`

### Expected traffic
- GSX-S750 + 890 Duke separately: low-volume long-tail; combined comparison post captures both simultaneously
- Indian drag scene audience: small but high-intent (searching specific model names + "quarter mile")
- EU/global comparison searchers who end up on Indian-market content via shared model names
- FastestLaps / AccelerationTimes have empty ET cells for both bikes — direct SERP gap

### Simulation numbers used
| Bike | Sim ET | Sim trap | Source |
|---|---|---|---|
| Suzuki GSX-S750 | 11.58 s | 193 km/h | MotoQuant litre_sport_600_1000 cluster |
| KTM 890 Duke 2020 | 11.42 s | 196 km/h | MotoQuant litre_sport_600_1000 cluster |

Real-world MCN benchmark for GSX-S750: 11.4 s @ 194 km/h (Nov 2017 road test).
Sim delta vs MCN: +0.18 s — within documented +0.15–0.22 s bias band. ✓

KTM 890 Duke benchmark: no published quarter-mile; KTM factory 0-100 claim 3.1 s → inferred ~11.3–11.5 s range. Sim at 11.42 s sits inside that range. ✓

### Internal links placed
1. /blog/cfmoto-800nk-quarter-mile-physics — LC8c parallel-twin context
2. /blog/the-physics-of-a-perfect-launch — launch physics primer
3. /blog/how-to-tune-for-aamby-valley-in-november — venue conditions reference
4. /blog/hayabusa-vs-zx-14r-which-is-faster — same comparison format at hyper-sport class
5. /bikes — catalog link with entity context
6. /pricing — commercial link

### Physics integrity checks
- GSX-S750 spec: 114 hp @ 10,500 rpm / 81 Nm @ 9,000 rpm, dry 193 kg, gear ratios [2.615, 1.882, 1.500, 1.261, 1.103, 0.966], 16F/45R — from known_bikes_extended.py (confirmed via Suzuki service manual 99500-36160-03E, cited in spec file)
- KTM 890 Duke spec: 105 hp @ 8,000 rpm / 92 Nm @ 6,500 rpm, dry 166 kg, gear ratios [2.625, 1.941, 1.580, 1.346, 1.185, 1.071], 15F/42R — from known_bikes_extended.py (confirmed via KTM service manual KTM-TI-2020-890D, cited in spec file)
- Power-to-weight ratios verified: GSX-S750 = 114/193 = 0.591 hp/kg; 890 Duke = 105/166 = 0.633 hp/kg ✓
- Reference baselines NOT quoted in the post (not relevant to mid-cc comparison — no K5/R1/Hayabusa mentions) ✓
- No AI-tell phrases used ✓

### Content structure
- Word count: ~2,200 words of body content
- H2 sections: 8 (meets ≥3 requirement) ✓
- Tables: 4 (1 main comparison, 1 section-by-section, 2 parts cost-per-tenth) ✓
- Simulator CTA: present at bottom pointing at /simulator ✓
- StructuredData articleSchema block: present ✓
- Internal links: 6 (meets ≥2+1+1 requirement) ✓
- ₹ pricing throughout (not $) ✓
- km/h throughout (not mph) ✓
- Opening hook has specific number (11.58 seconds) in first 15 words ✓

### Files touched
- web/app/blog/suzuki-gsx-s750-vs-ktm-890-duke-quarter-mile/page.js (NEW)
- web/app/blog/page.js (prepended new post to POSTS array)
- web/app/sitemap.js (added new slug with priority 0.83)
- reports/content_suzuki-gsx-s750-vs-ktm-890-duke-quarter-mile_2026-05-18.md (this file)
