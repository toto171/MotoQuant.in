#!/usr/bin/env node
/**
 * build.mjs — generates the IGNITION design-system preview cards.
 *
 * Each card is a self-contained HTML file whose FIRST LINE is a
 * `<!-- @dsCard group="…" -->` marker (consumed by the claude.ai/design
 * pane). Run `node build.mjs` from this directory; files land alongside.
 *
 * Tokens here mirror web/DESIGN.md §2 — if they drift, DESIGN.md wins.
 */
import { writeFileSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = dirname(fileURLToPath(import.meta.url));

const FONTS = `<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">`;

const BASE_CSS = `
:root{
  --a0:#050506; --a1:#0A0A0B; --a2:#111113; --a3:#1A1A1D; --a4:#27272A;
  --volt:#FF5E1F; --volt-b:#FF8F57; --volt-d:#CC4000;
  --go:#22C55E; --stage:#F59E0B; --foul:#EF4444; --mint:#00FFB2;
  --line:rgba(255,255,255,.08); --line2:rgba(255,255,255,.2);
  --t1:#FFFFFF; --t2:rgba(255,255,255,.65); --t3:rgba(255,255,255,.4);
}
*{box-sizing:border-box}
body{background:var(--a0);color:var(--t2);font-family:'Inter',system-ui,sans-serif;
  margin:0;padding:28px;font-size:14px;line-height:1.55;-webkit-font-smoothing:antialiased}
.disp{font-family:'Space Grotesk',system-ui,sans-serif;
  color:var(--t1);letter-spacing:-.01em;line-height:.95}
.mono{font-family:'JetBrains Mono',ui-monospace,monospace;font-variant-numeric:tabular-nums}
.label{font-family:'JetBrains Mono',ui-monospace,monospace;font-size:10px;
  text-transform:uppercase;letter-spacing:.25em;color:var(--t3)}
.card{background:rgba(16,20,27,.8);border:1px solid var(--line);border-radius:12px;padding:20px}
.dots{display:inline-flex;gap:5px;align-items:center}
.dot{width:6px;height:6px;border-radius:99px}
.dot-s{background:var(--stage)} .dot-g{background:var(--go)}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;height:44px;
  padding:0 20px;border-radius:8px;font-family:'Space Grotesk',system-ui,sans-serif;
  font-weight:700;font-size:14px;
  border:1px solid transparent;cursor:pointer;background:none;color:var(--t1)}
.btn-primary{background:var(--volt);color:#000}
.btn-primary:hover{background:var(--volt-b)}
.btn-ghost{border-color:rgba(255,255,255,.12);color:rgba(255,255,255,.85)}
.btn-ghost:hover{border-color:rgba(255,255,255,.3)}
.btn-danger{border-color:rgba(239,68,68,.4);background:rgba(239,68,68,.1);color:var(--foul)}
.btn-running{border-color:rgba(245,158,11,.4);background:rgba(245,158,11,.1);color:var(--stage)}
.btn-sm{height:36px;padding:0 14px;font-size:13px}
.btn[disabled]{opacity:.4;cursor:not-allowed}
.chip{display:inline-flex;align-items:center;height:24px;padding:0 8px;border-radius:4px;
  font-family:'JetBrains Mono',monospace;font-size:10px;text-transform:uppercase;
  letter-spacing:.2em;border:1px solid var(--line);color:var(--t2)}
.chip-volt{border-color:rgba(255,94,31,.35);background:rgba(255,94,31,.08);color:var(--volt)}
.chip-go{border-color:rgba(34,197,94,.35);background:rgba(34,197,94,.08);color:var(--go)}
.chip-stage{border-color:rgba(245,158,11,.35);background:rgba(245,158,11,.08);color:var(--stage)}
.chip-foul{border-color:rgba(239,68,68,.35);background:rgba(239,68,68,.08);color:var(--foul)}
.chip-mint{border-color:rgba(0,255,178,.35);background:rgba(0,255,178,.08);color:var(--mint)}
.input{height:44px;width:100%;border-radius:8px;border:1px solid var(--line);
  background:var(--a3);padding:0 14px;font-size:14px;color:var(--t1);outline:none;font-family:'Inter',sans-serif}
.input:focus{border-color:rgba(255,94,31,.55);box-shadow:0 0 0 1px rgba(255,94,31,.35)}
.timeslip{background:var(--a1);position:relative;padding:20px 22px;
  border-left:1px solid var(--line);border-right:1px solid var(--line)}
.timeslip::before,.timeslip::after{content:'';position:absolute;left:0;right:0;height:1px;
  background-image:repeating-linear-gradient(90deg,rgba(255,255,255,.28) 0 6px,transparent 6px 12px)}
.timeslip::before{top:0}.timeslip::after{bottom:0}
.ts-row{display:flex;justify-content:space-between;padding:7px 0;
  border-bottom:1px dashed rgba(255,255,255,.1);font-family:'JetBrains Mono',monospace;
  font-size:13px;font-variant-numeric:tabular-nums}
.ts-row:last-child{border-bottom:0}
.centerline{height:1px;background-image:repeating-linear-gradient(90deg,rgba(255,255,255,.15) 0 8px,transparent 8px 16px);margin:20px 0}
.delta-down{color:var(--go)} .delta-up{color:var(--foul)}
h3.section{font-family:'JetBrains Mono',monospace;font-size:10px;letter-spacing:.25em;
  text-transform:uppercase;color:var(--t3);font-weight:500;margin:26px 0 12px}
h3.section:first-of-type{margin-top:0}
`;

function page(title, group, body, extraCss = '') {
  return `<!-- @dsCard group="${group}" -->
<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${title}</title>${FONTS}<style>${BASE_CSS}${extraCss}</style></head>
<body>${body}</body></html>`;
}

const files = {};

/* ───────────────────────── Foundations ───────────────────────── */

files['foundations/colors.html'] = page('Colors', 'Foundations', `
<h3 class="section">Asphalt — surfaces</h3>
<div style="display:flex;gap:10px;flex-wrap:wrap">
  ${[['asphalt-0','#050506','page'],['asphalt-1','#0A0A0B','timeslip'],['asphalt-2','#111113','card'],['asphalt-3','#1A1A1D','input'],['asphalt-4','#27272A','hover line']]
    .map(([n,h,use])=>`<div style="width:118px"><div style="height:64px;border-radius:10px;background:${h};border:1px solid var(--line)"></div>
    <div class="mono" style="font-size:11px;color:var(--t1);margin-top:8px">${h}</div>
    <div class="label" style="margin-top:2px">${n}</div><div style="font-size:11px;color:var(--t3)">${use}</div></div>`).join('')}
</div>
<h3 class="section">Accent — Signal orange (the needle past redline)</h3>
<div style="display:flex;gap:10px;flex-wrap:wrap">
  ${[['accent','#FF5E1F','primary action'],['accent-bright','#FF8F57','hover'],['accent-deep','#CC4000','borders / pressed']]
    .map(([n,h,use])=>`<div style="width:118px"><div style="height:64px;border-radius:10px;background:${h}"></div>
    <div class="mono" style="font-size:11px;color:var(--t1);margin-top:8px">${h}</div>
    <div class="label" style="margin-top:2px">${n}</div><div style="font-size:11px;color:var(--t3)">${use}</div></div>`).join('')}
</div>
<h3 class="section">Signal — meaning only, never decoration</h3>
<div style="display:flex;gap:10px;flex-wrap:wrap">
  ${[['signal-go','#22C55E','success · faster · PB'],['signal-stage','#F59E0B','running · warning · estimated'],['signal-foul','#EF4444','error · slower'],['mint','#00FFB2','PRO / Studio chips only']]
    .map(([n,h,use])=>`<div style="width:140px"><div style="height:64px;border-radius:10px;background:${h}"></div>
    <div class="mono" style="font-size:11px;color:var(--t1);margin-top:8px">${h}</div>
    <div class="label" style="margin-top:2px">${n}</div><div style="font-size:11px;color:var(--t3)">${use}</div></div>`).join('')}
</div>
<div class="centerline"></div>
<p style="max-width:560px;font-size:12.5px;color:var(--t3)">Discipline (the kit rule): orange is reserved for the moving parts —
the primary action, live data, at most one accent detail per viewport. Text is white on asphalt. Signal colors carry
state (delta, status, tier) and are never used to decorate.</p>
`);

files['foundations/type.html'] = page('Typography', 'Foundations', `
<h3 class="section">Display — Space Grotesk · sentence case</h3>
<div class="disp" style="font-size:64px;font-weight:700">Know your time<br>before you <span style="color:var(--volt)">stage</span></div>
<div class="disp" style="font-size:34px;font-weight:600;margin-top:18px">Section heading — build the slip</div>
<div class="disp" style="font-size:21px;font-weight:600;margin-top:12px">Card title voice</div>
<h3 class="section">Body — Inter</h3>
<p style="max-width:520px;margin:0">Physics-based quarter-mile simulation — not a power-to-weight
formula. 541 bikes with real dyno curves, gear cassettes and aero. Built for the Indian strip:
INR pricing, Aamby Valley to Kari.</p>
<h3 class="section">Data — JetBrains Mono · tabular</h3>
<div style="display:flex;align-items:baseline;gap:26px;flex-wrap:wrap">
  <div><div class="mono" style="font-size:52px;font-weight:700;color:var(--t1)">10.0334<span style="font-size:20px;color:var(--t3)">s</span></div><div class="label">Elapsed time</div></div>
  <div><div class="mono" style="font-size:30px;font-weight:500;color:var(--t1)">237.4</div><div class="label">Trap km/h</div></div>
  <div><div class="mono" style="font-size:30px;font-weight:500;color:var(--go)">−0.213s</div><div class="label">Delta (faster)</div></div>
</div>
<h3 class="section">Label voice</h3>
<div class="label">Quarter mile · Aamby Valley · 28°C</div>
<div class="centerline"></div>
<p style="max-width:560px;font-size:12.5px;color:var(--t3)">Rule: numbers the rider cares about are mono and big.
Section names are condensed uppercase. Everything else is quiet Inter — never uppercase.</p>
`);

files['foundations/surfaces.html'] = page('Surfaces & spacing', 'Foundations', `
<h3 class="section">Card — the standard panel</h3>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;max-width:640px">
  <div class="card"><div class="label" style="margin-bottom:8px">Standard card</div>
    <div class="disp" style="font-size:20px;font-weight:600">Build optimizer</div>
    <p style="font-size:13px;margin:6px 0 0">radius 12 · border white/8 · asphalt-2/80</p></div>
  <div class="card" style="border-color:var(--line2)"><div class="label" style="margin-bottom:8px">Hover state</div>
    <div class="disp" style="font-size:20px;font-weight:600">Border lifts to white/20</div>
    <p style="font-size:13px;margin:6px 0 0">plus 2px translate — reduced-motion safe</p></div>
</div>
<h3 class="section">Centerline divider — the strip motif</h3>
<div style="max-width:640px"><div class="centerline"></div></div>
<h3 class="section">Rhythm</h3>
<p style="max-width:560px;font-size:13px">Sections py-16/24 · containers max-w-6xl · card padding 20/24 ·
grid gap 16/24 · never more than two stacked surface levels.</p>
`);

/* ───────────────────────── Components ───────────────────────── */

files['components/stage-dots.html'] = page('Stage dots', 'Components', `
<h3 class="section">The signature motif — pre-stage · stage · go</h3>
<div style="display:flex;flex-direction:column;gap:22px">
  <div class="dots"><span class="dot dot-s"></span><span class="dot dot-s"></span><span class="dot dot-g"></span></div>
  <div style="display:flex;align-items:center;gap:10px">
    <span class="dots"><span class="dot dot-s"></span><span class="dot dot-s"></span><span class="dot dot-g"></span></span>
    <span class="label">Section eyebrow voice</span>
  </div>
  <div style="display:flex;align-items:center;gap:10px">
    <span class="dots"><span class="dot dot-s"></span><span class="dot dot-s"></span><span class="dot" style="background:var(--foul)"></span></span>
    <span class="label" style="color:var(--foul)">Foul variant — errors and 404 only</span>
  </div>
</div>
<div class="centerline"></div>
<p style="max-width:560px;font-size:12.5px;color:var(--t3)">Used as section eyebrows, list bullets and loading
accents. One animated light-up (amber→amber→green, opacity only) per page maximum — in the hero.
This is the only decorative ornament in the system.</p>
`);

files['components/buttons.html'] = page('Buttons', 'Components', `
<h3 class="section">Primary — the signal</h3>
<div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap">
  <button class="btn btn-primary">Run a sim</button>
  <button class="btn btn-primary btn-sm">Save this run</button>
  <button class="btn btn-primary" disabled>Run a sim</button>
</div>
<h3 class="section">Ghost / secondary</h3>
<div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap">
  <button class="btn btn-ghost">Browse 541 bikes</button>
  <button class="btn btn-ghost btn-sm">Share</button>
</div>
<h3 class="section">Running (staged) → stop affordance</h3>
<div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap">
  <button class="btn btn-running" style="position:relative;overflow:hidden">■ Stop — 42%
    <span style="position:absolute;left:0;bottom:0;height:2px;width:42%;background:var(--stage)"></span></button>
  <button class="btn btn-danger">Revoke key</button>
</div>
<div class="centerline"></div>
<p style="max-width:560px;font-size:12.5px;color:var(--t3)">One run/stop pattern sitewide: idle volt →
amber running with live % and edge strip → hover flips to foul red for stop. Text on volt is near-black.</p>
`);

files['components/inputs.html'] = page('Inputs & chips', 'Components', `
<div style="max-width:420px">
<h3 class="section">Text / search</h3>
<input class="input" placeholder="Search 541 bikes — try 'Hayabusa'">
<div style="height:12px"></div>
<input class="input" style="border-color:rgba(255,94,31,.55);box-shadow:0 0 0 1px rgba(255,94,31,.35)" value="Kawasaki Ninja ZX-10R">
<h3 class="section">Select + slider</h3>
<select class="input"><option>Aamby Valley — 640m DA</option></select>
<div style="margin-top:18px">
  <div style="display:flex;justify-content:space-between;margin-bottom:6px">
    <span class="label">Budget</span><span class="mono" style="font-size:12px;color:var(--t1)">₹1,50,000</span></div>
  <div style="height:4px;border-radius:99px;background:var(--a4);position:relative">
    <div style="position:absolute;left:0;top:0;bottom:0;width:38%;background:var(--volt);border-radius:99px"></div>
    <div style="position:absolute;left:38%;top:50%;width:16px;height:16px;border-radius:99px;background:var(--t1);transform:translate(-50%,-50%)"></div>
  </div>
</div>
<h3 class="section">Chips</h3>
<div style="display:flex;gap:8px;flex-wrap:wrap">
  <span class="chip">520 chain</span>
  <span class="chip chip-volt">Popular</span>
  <span class="chip chip-go">−0.21s faster</span>
  <span class="chip chip-stage">Estimated</span>
  <span class="chip chip-foul">+0.13s slower</span>
  <span class="chip chip-mint">Studio</span>
</div>
</div>
`);

files['components/stat-tiles.html'] = page('Stat tiles', 'Components', `
<h3 class="section">Catalog strip</h3>
<div style="display:grid;grid-template-columns:repeat(6,1fr);gap:12px;max-width:760px">
  ${[['541','Bikes'],['254','Tires'],['593','Parts'],['20','Venues'],['4393','Tests'],['15','Sub-models']]
    .map(([n,l])=>`<div style="text-align:center;padding:14px 4px;border:1px solid var(--line);border-radius:10px;background:var(--a1)">
      <div class="mono" style="font-size:24px;font-weight:700;color:var(--t1)">${n}</div>
      <div class="label" style="margin-top:4px">${l}</div></div>`).join('')}
</div>
<h3 class="section">Accuracy tiles (proof section)</h3>
<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;max-width:640px">
  ${[['221','Published benchmarks'],['82','Within ±0.10s'],['137','Within ±0.20s'],['±0.006s','Top-10 mean error']]
    .map(([n,l])=>`<div class="card" style="padding:16px">
      <div class="mono" style="font-size:26px;font-weight:700;color:var(--volt)">${n}</div>
      <div style="font-size:11.5px;color:var(--t3);margin-top:4px">${l}</div></div>`).join('')}
</div>
`);

files['components/timeslip.html'] = page('Timeslip', 'Components', `
<div style="max-width:360px">
<div class="timeslip">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
    <span class="label">MotoQuant timing</span>
    <span class="dots"><span class="dot dot-s"></span><span class="dot dot-s"></span><span class="dot dot-g"></span></span>
  </div>
  <div class="disp" style="font-size:22px;font-weight:600">Suzuki Hayabusa</div>
  <div class="label" style="margin:2px 0 14px">Aamby Valley · 28°C · DA 640m</div>
  <div class="mono" style="font-size:56px;font-weight:700;color:var(--t1);line-height:1">10.471<span style="font-size:22px;color:var(--t3)">s</span></div>
  <div class="label" style="margin:4px 0 14px">Quarter mile · trap 237.4 km/h</div>
  <div class="ts-row"><span style="color:var(--t3)">60 FT</span><span style="color:var(--t1)">1.782</span></div>
  <div class="ts-row"><span style="color:var(--t3)">330 FT</span><span style="color:var(--t1)">4.412</span></div>
  <div class="ts-row"><span style="color:var(--t3)">1/8 MI</span><span style="color:var(--t1)">6.653 @ 189.2</span></div>
  <div class="ts-row"><span style="color:var(--t3)">1000 FT</span><span style="color:var(--t1)">8.601</span></div>
  <div class="ts-row"><span style="color:var(--t3)">1/4 MI</span><span style="color:var(--volt)">10.471 @ 237.4</span></div>
</div>
<div style="display:flex;gap:10px;margin-top:16px">
  <button class="btn btn-primary btn-sm" style="flex:1">Share slip</button>
  <button class="btn btn-ghost btn-sm" style="flex:1">Save run</button>
</div>
</div>
`);

files['components/progress.html'] = page('Progress', 'Components', `
<div style="max-width:440px">
<h3 class="section">Determinate — job with live %</h3>
<div class="card" style="padding:16px">
  <div style="display:flex;justify-content:space-between;margin-bottom:8px">
    <span class="label" style="color:var(--stage)">Sweeping gearing</span>
    <span class="mono" style="font-size:12px;color:var(--t1)">64%</span></div>
  <div style="height:4px;border-radius:99px;background:var(--a4)">
    <div style="height:4px;width:64%;border-radius:99px;background:var(--volt)"></div></div>
</div>
<h3 class="section">Staged — unknown duration</h3>
<div class="card" style="padding:16px">
  <div class="label" style="margin-bottom:8px;color:var(--stage)">Waking the simulation engine — free-tier cold start</div>
  <div style="height:4px;border-radius:99px;background:var(--a4);overflow:hidden;position:relative">
    <div style="position:absolute;height:4px;width:30%;left:20%;border-radius:99px;background:var(--volt);opacity:.8"></div></div>
</div>
<h3 class="section">Skeleton</h3>
<div class="card" style="padding:16px;display:flex;flex-direction:column;gap:10px">
  ${[68,42,55].map(w=>`<div style="height:12px;width:${w}%;border-radius:6px;background:rgba(255,255,255,.06)"></div>`).join('')}
</div>
</div>
`);

files['components/nav.html'] = page('Navigation', 'Components', `
<h3 class="section">Desktop nav</h3>
<div style="border:1px solid var(--line);border-radius:12px;background:rgba(7,9,12,.9);padding:0 20px;height:64px;display:flex;align-items:center;gap:22px;max-width:960px">
  <div style="display:flex;align-items:center;gap:10px">
    <span class="dots"><span class="dot dot-s"></span><span class="dot dot-s"></span><span class="dot dot-g"></span></span>
    <span class="disp" style="font-size:20px;font-weight:700;letter-spacing:.04em">MotoQuant</span>
  </div>
  <div style="display:flex;gap:18px;font-size:13px;color:var(--t2);margin-left:8px">
    <span style="color:var(--t1)">Simulator</span><span>Optimize</span><span>Autotune</span><span>Bikes</span><span>Leaderboard</span><span>Pricing</span><span>Resources ▾</span>
  </div>
  <div style="margin-left:auto;display:flex;gap:12px;align-items:center">
    <span class="chip">⌘K</span>
    <span style="font-size:13px">Sign in</span>
    <button class="btn btn-primary btn-sm">Run a sim</button>
  </div>
</div>
<h3 class="section">Mobile tool bar (bottom, tool routes only)</h3>
<div style="border:1px solid var(--line);border-radius:14px;background:rgba(7,9,12,.95);padding:10px 6px;display:flex;max-width:390px">
  ${[['Sim',1],['Optimize',0],['Autotune',0],['Bikes',0],['Board',0]]
    .map(([l,on])=>`<div style="flex:1;text-align:center">
      <div style="width:22px;height:22px;border-radius:6px;margin:0 auto 4px;background:${on?'rgba(255,94,31,.18)':'var(--a3)'};border:1px solid ${on?'rgba(255,94,31,.5)':'var(--line)'}"></div>
      <div class="label" style="letter-spacing:.12em;color:${on?'var(--volt)':'var(--t3)'}">${l}</div></div>`).join('')}
</div>
`);

files['components/leaderboard.html'] = page('Leaderboard rows', 'Components', `
<div style="max-width:680px;display:flex;flex-direction:column;gap:10px">
${[
  ['01','Kawasaki Ninja H2R','8.912','241.8','Aamby Valley',1],
  ['02','Suzuki Hayabusa','9.211','229.6','MMRT',0],
  ['03','KTM Duke 390','13.509','173.0','Kari',0],
].map(([r,b,et,trap,v,pb])=>`
<div class="card" style="display:flex;align-items:center;gap:18px;padding:14px 18px">
  <span class="mono" style="font-size:13px;color:var(--t3)">${r}</span>
  <div style="flex:1;min-width:0">
    <div class="disp" style="font-size:18px;font-weight:600">${b}</div>
    <div style="display:flex;gap:8px;margin-top:3px"><span class="chip" style="height:20px">${v}</span>${pb?'<span class="chip chip-go" style="height:20px">PB</span>':''}</div>
  </div>
  <div style="text-align:right">
    <div class="mono" style="font-size:24px;font-weight:700;color:var(--t1)">${et}<span style="font-size:13px;color:var(--t3)">s</span></div>
    <div class="label" style="letter-spacing:.15em">${trap} km/h</div>
  </div>
</div>`).join('')}
</div>
`);

/* ───────────────────────── Patterns ───────────────────────── */

files['patterns/landing-hero.html'] = page('Landing hero', 'Patterns', `
<div style="position:relative;padding:48px 8px 40px;max-width:1040px;overflow:hidden">
  <div style="position:absolute;left:50%;top:0;bottom:0;width:1px;background-image:repeating-linear-gradient(180deg,rgba(255,255,255,.07) 0 10px,transparent 10px 22px)"></div>
  <div style="position:absolute;inset:0;background:radial-gradient(ellipse 60% 45% at 30% 0%,rgba(255,94,31,.06),transparent 70%)"></div>
  <div style="position:relative;display:grid;grid-template-columns:1.15fr .85fr;gap:44px;align-items:center">
    <div>
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:18px">
        <span class="dots"><span class="dot dot-s"></span><span class="dot dot-s"></span><span class="dot dot-g"></span></span>
        <span class="label">Physics-based · free during beta</span>
      </div>
      <div class="disp" style="font-size:54px;font-weight:700;letter-spacing:-0.02em">Know your time<br>before you <span style="color:var(--volt)">stage</span></div>
      <p style="max-width:440px;margin:18px 0 24px;font-size:15px">Full quarter-mile physics for 541 bikes —
      real dyno curves, gears and aero. Indian strips, parts priced in ₹, slips you can share on WhatsApp.</p>
      <div style="display:flex;gap:12px">
        <button class="btn btn-primary">Run a sim</button>
        <button class="btn btn-ghost">Browse 541 bikes</button>
      </div>
    </div>
    <div class="card" style="padding:18px">
      <div class="label" style="margin-bottom:10px">Quick sim</div>
      <input class="input" value="Suzuki Hayabusa" readonly>
      <div style="height:10px"></div>
      <select class="input"><option>Aamby Valley</option></select>
      <div style="height:14px"></div>
      <button class="btn btn-primary" style="width:100%">Simulate quarter mile</button>
      <div style="display:flex;justify-content:space-between;align-items:baseline;margin-top:16px">
        <div><div class="mono" style="font-size:34px;font-weight:700;color:var(--t1)">10.471<span style="font-size:15px;color:var(--t3)">s</span></div><div class="label">ET</div></div>
        <div style="text-align:right"><div class="mono" style="font-size:20px;color:var(--t1)">237.4</div><div class="label">Trap km/h</div></div>
      </div>
    </div>
  </div>
</div>
`);

files['patterns/tool-workbench.html'] = page('Tool workbench', 'Patterns', `
<div style="max-width:1040px">
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">
    <span class="dots"><span class="dot dot-s"></span><span class="dot dot-s"></span><span class="dot dot-g"></span></span>
    <span class="label">Build optimizer</span>
  </div>
  <div class="disp" style="font-size:40px;font-weight:700;margin-bottom:22px">Fastest build for the budget</div>
  <div style="display:grid;grid-template-columns:.9fr 1.1fr;gap:20px">
    <div style="display:flex;flex-direction:column;gap:14px">
      <div class="card"><div class="label" style="margin-bottom:10px">Bike</div><input class="input" value="Suzuki Hayabusa" readonly></div>
      <div class="card"><div class="label" style="margin-bottom:10px">Budget</div>
        <div class="mono" style="font-size:22px;color:var(--t1);margin-bottom:10px">₹1,50,000</div>
        <div style="height:4px;border-radius:99px;background:var(--a4)"><div style="height:4px;width:38%;border-radius:99px;background:var(--volt)"></div></div>
        <div style="display:flex;gap:8px;margin-top:12px"><span class="chip">₹50k</span><span class="chip chip-volt">₹1.5L</span><span class="chip">₹5L</span><span class="chip">Outlaw — no limit</span></div>
      </div>
      <button class="btn btn-primary" style="width:100%">Optimise build</button>
    </div>
    <div class="card" style="padding:20px">
      <div style="display:flex;justify-content:space-between;align-items:baseline">
        <div><div class="label">Base → optimised</div>
          <div class="mono" style="font-size:30px;font-weight:700;color:var(--t1);margin-top:6px">10.471 → 9.988<span style="font-size:14px;color:var(--t3)">s</span></div></div>
        <span class="chip chip-go" style="height:28px;font-size:12px">−0.483s</span>
      </div>
      <div class="centerline"></div>
      <div class="ts-row"><span>Akrapovic Racing full system</span><span style="color:var(--go)">−0.211s · ₹2,38,000</span></div>
      <div class="ts-row"><span>ECU flash — full race</span><span style="color:var(--go)">−0.148s · ₹18,500</span></div>
      <div class="ts-row"><span>520 conversion 17/45</span><span style="color:var(--go)">−0.124s · ₹9,200</span></div>
      <div style="display:flex;justify-content:space-between;margin-top:14px">
        <span class="label">Cost per tenth</span><span class="mono" style="font-size:13px;color:var(--t1)">₹55,090</span>
      </div>
    </div>
  </div>
</div>
`);

for (const [rel, html] of Object.entries(files)) {
  const p = join(ROOT, rel);
  mkdirSync(dirname(p), { recursive: true });
  writeFileSync(p, html);
  console.log('wrote', rel, html.length, 'bytes');
}
console.log(`\n${Object.keys(files).length} cards generated.`);
