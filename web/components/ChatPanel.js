'use client';

// ChatPanel — multi-turn natural-language chat for the agent-mode
// /api/chat surface. Self-contained; takes apiUrl as a prop so it can be
// reused by both the landing-page SimulatorWidget and the full /simulator
// page (signature unchanged — internally requests go through lib/api's
// chatJob, which shares the same API_URL base both callers pass in).
//
// July 2026 agent rework:
//   • Conversation transcript — the client holds [{role, content}] turns and
//     sends the last ~12 back with each request (the server is stateless).
//   • Job-backed by default (POST /api/jobs/chat → poll) with live stage text
//     ("Simulating Hayabusa…", "Optimizing stage_4…") and a ■ Stop button;
//     degrades to the sync /api/chat route on older backends.
//   • Per-type block renderers for the ordered `blocks` payloads: sim_result /
//     estimated_sim (amber ESTIMATED badge + assumptions) / top_speed /
//     compare_result / build_result / outlaw_result (tire stage + setup) /
//     autotune_result / web_citations; lookup blocks (parts / tires /
//     bike_details / venues) collapse to one-line chips.
//   • Error branches: assistant_unavailable, free_assistant_resting,
//     key_rejected, invalid_key_format, rate_limited, refused, agent_failed
//     (copy in lib/assistant.js), bike_not_found (suggestion chips), and a
//     catch-all that surfaces error_detail.
//
// November 2026, Claude assistants:
//   • An "Assistant" dropdown (1. The doctor, 2. The mechanic; default the
//     mechanic), remembered in localStorage. The server maps the id to a
//     Claude model; the browser never sends a model id.
//   • "Use your own key": the visitor's Anthropic key stays in this browser
//     (sessionStorage, or localStorage when "Remember on this device" is
//     ticked) and goes out as the X-Anthropic-Key header only on the request
//     that starts a chat. Helpers and tests: lib/assistant.js.
//   • GET /api/assistant on mount: when the free assistant is off, the key
//     disclosure opens with a short explanation.

import { useState, useRef, useEffect, useId } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import {
  AlertCircle, Send, KeyRound, RotateCcw, Timer, Link as LinkIcon, ChevronDown,
  ExternalLink,
} from 'lucide-react';
import SimProgress from './SimProgress';
import { chatJob, getAssistantInfo, partLabel } from '../lib/api';
import useAsyncTask from '../lib/useAsyncTask';
import {
  ASSISTANTS, ASSISTANT_EVENT, CONSOLE_KEYS_URL, assistantInfo, browserStores,
  chatErrorCopy, describeChatFailure, looksLikeAnthropicKey, maskKey, readAssistant,
  readKey, removeKey, saveAssistant, saveKey,
} from '../lib/assistant';

const CHAT_EXAMPLES = [
  'How fast is a Duke 390 at Aamby Valley?',
  'Compare a ZX-10R and an S1000RR',
  'Best parts for a Hayabusa with no budget limit',
];

// How many prior turns ride along with each request (server caps at 24).
const HISTORY_TURNS = 12;

// ─── formatting helpers ─────────────────────────────────────────────────────
const fmtNum = (v, d = 2) => (v == null ? '' : Number(v).toFixed(d));
const fmtINR = (n) =>
  n == null ? '' : `₹${Math.round(n).toLocaleString('en-IN')}`;

// ─── shared tile ────────────────────────────────────────────────────────────
function Tile({ label, value, accent = false }) {
  return (
    <div className="rounded-lg border border-white/10 bg-asphalt-3 p-3 text-center">
      <p className="mb-1 text-sm text-white/70">{label}</p>
      <p className={`font-display text-xl font-bold tabular-nums ${accent ? 'text-accent' : 'text-white'}`}>
        {value}
      </p>
    </div>
  );
}

function LookupChip({ label }) {
  return (
    <span className="chip text-white/70">
      {label}
    </span>
  );
}

// ─── block renderers ────────────────────────────────────────────────────────

// sim_result + estimated_sim share the 4-tile ET/trap/60ft/eighth layout;
// estimated adds the amber confidence badge + assumptions list.
function SimTiles({ payload, estimated = false }) {
  const conf =
    payload.confidence != null
      ? Math.round(
          payload.confidence <= 1 ? payload.confidence * 100 : payload.confidence
        )
      : null;
  const assumptions = Array.isArray(payload.assumptions) ? payload.assumptions : [];
  return (
    <div className="space-y-2">
      {(payload.bike_name || estimated) && (
        <div className="flex items-center gap-2 flex-wrap">
          {payload.bike_name && (
            <p className="text-sm font-medium text-white/80">{payload.bike_name}</p>
          )}
          {estimated && (
            <span className="chip chip-stage font-semibold">
              Estimate, not in our catalog{conf != null ? ` · ${conf}% confident` : ''}
            </span>
          )}
        </div>
      )}
      <div className="grid grid-cols-2 gap-3">
        {payload.et_quarter_s != null && (
          <Tile label="Quarter-mile time" value={`${fmtNum(payload.et_quarter_s)} s`} accent />
        )}
        {payload.trap_speed_kmh != null && (
          <Tile label="Finish-line speed" value={`${fmtNum(payload.trap_speed_kmh, 0)} km/h`} />
        )}
        {payload.et_60ft_s != null && (
          <Tile label="First 60 ft (launch)" value={`${fmtNum(payload.et_60ft_s)} s`} />
        )}
        {payload.et_eighth_s != null && (
          <Tile label="Halfway (⅛ mile)" value={`${fmtNum(payload.et_eighth_s)} s`} />
        )}
      </div>
      {estimated && payload.top_speed_kmh != null && (
        <p className="text-sm text-white/70">
          Top speed about {fmtNum(payload.top_speed_kmh, 0)} km/h
        </p>
      )}
      {Array.isArray(payload.modifications) && payload.modifications.length > 0 && (
        <p className="text-sm text-white/60">
          {payload.modifications.join(' · ')}
        </p>
      )}
      {estimated && assumptions.length > 0 && (
        <ul className="list-inside list-disc space-y-0.5 text-sm text-white/60">
          {assumptions.map((a, i) => (
            <li key={i}>{a}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

function TopSpeedTiles({ payload }) {
  return (
    <div className="space-y-2">
      {payload.bike_name && (
        <p className="text-sm font-medium text-white/80">{payload.bike_name}</p>
      )}
      <div className="grid grid-cols-3 gap-3">
        {payload.top_speed_kmh != null && (
          <Tile label="Top speed (km/h)" value={fmtNum(payload.top_speed_kmh, 0)} accent />
        )}
        {payload.terminal_gear != null && <Tile label="Gear" value={payload.terminal_gear} />}
        {payload.terminal_rpm != null && (
          <Tile label="Engine speed (rpm)" value={Math.round(payload.terminal_rpm).toLocaleString('en-IN')} />
        )}
      </div>
      {payload.reached_plateau === false && (
        <p className="text-sm text-white/60">
          Still gaining speed slowly when the run ended, so the true top speed may be a little higher.
        </p>
      )}
    </div>
  );
}

function CompareBlock({ payload }) {
  const a = payload.bike_a || {};
  const b = payload.bike_b || {};
  const delta = payload.delta_et_s;
  const rows = [
    ['Quarter-mile time', (v) => (v?.et_quarter_s != null ? `${fmtNum(v.et_quarter_s)} s` : '')],
    ['Finish-line speed', (v) => (v?.trap_speed_kmh != null ? `${fmtNum(v.trap_speed_kmh, 0)} km/h` : '')],
    ['First 60 ft (launch)', (v) => (v?.et_60ft_s != null ? `${fmtNum(v.et_60ft_s)} s` : '')],
  ].filter(([, get]) => get(a) || get(b));
  const aWins = payload.winner && payload.winner === a.bike_name;
  return (
    <div className="space-y-2 overflow-x-auto rounded-lg border border-white/10 bg-asphalt-3 p-3">
      {payload.winner && (
        <p className="text-sm font-medium text-signal-go">
          {payload.winner} is quicker{delta != null ? ` by ${Math.abs(delta).toFixed(2)} s` : ''}
        </p>
      )}
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left">
            <th className="pb-1.5 pr-2 font-medium text-white/70" scope="col">
              <span className="sr-only">Metric</span>
            </th>
            <th className={`pb-1.5 pr-2 font-medium ${aWins ? 'text-accent' : 'text-white/70'}`} scope="col">
              {a.bike_name || 'Bike A'}
            </th>
            <th className={`pb-1.5 font-medium ${!aWins && payload.winner ? 'text-accent' : 'text-white/70'}`} scope="col">
              {b.bike_name || 'Bike B'}
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map(([label, get]) => (
            <tr key={label} className="border-t border-white/10">
              <td className="py-1.5 pr-2 text-white/70">{label}</td>
              <td className="py-1.5 pr-2 font-mono tabular-nums text-white">{get(a)}</td>
              <td className="py-1.5 font-mono tabular-nums text-white">{get(b)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// Shared parts-list + totals renderer for build_result and outlaw_result.
// baseEt → finalEt reads left-to-right; the diff chip is finalEt − baseEt so
// negative (green) always means faster, regardless of the payload's own
// delta-sign convention.
function BuildSummary({
  title, bikeName, baseEt, finalEt, costInr, budgetLabel, parts, extraLines,
}) {
  const diff = baseEt != null && finalEt != null ? finalEt - baseEt : null;
  return (
    <div className="space-y-3 rounded-lg border border-white/10 bg-asphalt-3 p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm font-medium text-white/85">
          {title}
          {bikeName ? <span className="text-white/60"> · {bikeName}</span> : null}
        </p>
        <p className="text-sm text-white/60">
          Budget: <span className="text-white/85">{budgetLabel}</span>
        </p>
      </div>

      <div className="flex flex-wrap items-baseline gap-2">
        <span className="font-display text-base tabular-nums text-white/60">{fmtNum(baseEt)} s</span>
        <span className="text-xs text-white/50" aria-hidden="true">→</span>
        <span className="font-display text-2xl font-bold tabular-nums text-accent">{fmtNum(finalEt)} s</span>
        {diff != null && diff !== 0 && (
          <span className={`text-sm font-medium tabular-nums ${diff < 0 ? 'text-signal-go' : 'text-signal-foul'}`}>
            {Math.abs(diff).toFixed(2)} s {diff < 0 ? 'quicker' : 'slower'}
          </span>
        )}
        {costInr != null && (
          <span className="ml-auto text-sm tabular-nums text-white/70">{fmtINR(costInr)}</span>
        )}
      </div>

      {Array.isArray(extraLines) && extraLines.length > 0 && (
        <div className="space-y-1">
          {extraLines.map((line, i) => (
            <p key={i} className="text-sm text-white/70">
              <span className="mr-2 font-medium text-white/85">{line.label}</span>
              {line.text}
            </p>
          ))}
        </div>
      )}

      {parts.length > 0 && (
        <div className="space-y-1">
          {parts.map((p, i) => (
            <div
              key={p.part_id ?? i}
              className="flex items-center justify-between gap-3 rounded-lg border border-white/10 px-2.5 py-2"
            >
              <p className="min-w-0 truncate text-sm text-white/85">{partLabel(p.brand, p.name)}</p>
              <p className="shrink-0 text-sm tabular-nums text-white/70">
                {fmtINR(p.price_inr ?? p.price)}
                {p.delta_et_s != null && (
                  /* delta_et_s = with-part − without: negative = quicker. */
                  <span className={`ml-2 ${Number(p.delta_et_s) < 0 ? 'text-signal-go' : 'text-white/60'}`}>
                    {Number(p.delta_et_s) < 0
                      ? `${Math.abs(Number(p.delta_et_s)).toFixed(2)} s quicker`
                      : `${Number(p.delta_et_s).toFixed(2)} s slower`}
                  </span>
                )}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

const SEVERITY_WORDS = { info: 'Note', warning: 'Heads up', critical: 'Important' };

// Warnings arrive as {severity, message} from the optimiser, or as plain
// strings from the compact summary the agent builds.
function warningParts(w) {
  if (typeof w === 'string') return { severity: 'warning', message: w };
  return { severity: w?.severity || 'warning', message: w?.message || '' };
}

// next_upgrade: {part:{brand,name,price_inr}, marginal_cost_inr,
// marginal_et_gain_s (positive = quicker), reason} from the optimiser, or a
// flat {brand, name, price_inr|price, delta_et_s (negative = quicker), reason}.
function nextUpgradeParts(nu) {
  if (!nu || typeof nu !== 'object') return null;
  const part = nu.part && typeof nu.part === 'object' ? nu.part : nu;
  const label = partLabel(part.brand, part.name);
  if (!label) return null;
  const cost = nu.marginal_cost_inr ?? part.price_inr ?? part.price ?? null;
  let quicker = null;
  if (nu.marginal_et_gain_s != null) quicker = Number(nu.marginal_et_gain_s);
  else if (part.delta_et_s != null) quicker = -Number(part.delta_et_s);
  return { label, cost, quicker, reason: nu.reason || '' };
}

function BuildBlock({ payload }) {
  const noLimit =
    payload.budget_unlimited === true || Number(payload.budget_inr) >= 5_000_000;
  const warnings = (Array.isArray(payload.warnings) ? payload.warnings : [])
    .map(warningParts)
    .filter((w) => w.message);
  const synergies = (Array.isArray(payload.synergies) ? payload.synergies : [])
    .map((x) => (typeof x === 'string' ? x : x?.description))
    .filter(Boolean);
  const next = nextUpgradeParts(payload.next_upgrade);
  return (
    <div className="space-y-2">
      <BuildSummary
        title={payload.tier_label || 'Best parts for your budget'}
        bikeName={payload.bike_name}
        baseEt={payload.base_et_s}
        finalEt={payload.optimized_et_s}
        costInr={payload.total_cost_inr}
        budgetLabel={noLimit ? 'No limit' : fmtINR(payload.budget_inr)}
        parts={payload.parts || []}
      />
      {synergies.length > 0 && (
        <div className="rounded-lg border border-white/10 bg-asphalt-3 p-3">
          <p className="mb-1 text-sm font-medium text-white/85">Parts that work well together</p>
          <ul className="space-y-1 text-sm text-white/70">
            {synergies.map((t, i) => (
              <li key={i}>{t}</li>
            ))}
          </ul>
        </div>
      )}
      {warnings.length > 0 && (
        <div className="rounded-lg border border-white/10 bg-asphalt-3 p-3">
          <p className="mb-1.5 text-sm font-medium text-white/85">Things to check</p>
          <ul className="space-y-1.5">
            {warnings.map((w, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-white/75">
                <span className={`chip shrink-0 ${w.severity === 'critical' ? 'chip-foul' : 'chip-stage'}`}>
                  {SEVERITY_WORDS[w.severity] || 'Note'}
                </span>
                <span className="min-w-0">{w.message}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
      {next && (
        <div className="rounded-lg border border-white/10 bg-asphalt-3 p-3">
          <p className="mb-1 text-sm font-medium text-white/85">If you have more to spend</p>
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <p className="text-sm text-white">{next.label}</p>
              {next.reason && <p className="mt-0.5 text-sm text-white/65">{next.reason}</p>}
            </div>
            <div className="shrink-0 text-right text-sm tabular-nums">
              {next.cost != null && <p className="text-white/85">+{fmtINR(next.cost)}</p>}
              {next.quicker != null && next.quicker > 0 && (
                <p className="text-signal-go">{next.quicker.toFixed(2)} s quicker</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// rank_result: the quickest catalog bikes for a filter, each fully simulated.
function RankBlock({ payload }) {
  const rows = Array.isArray(payload.ranking) ? payload.ranking : [];
  if (rows.length === 0) return null;
  return (
    <div className="space-y-2 overflow-x-auto rounded-lg border border-white/10 bg-asphalt-3 p-3">
      <p className="text-sm font-medium text-white/85">Quickest bikes</p>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left">
            <th scope="col" className="pb-1.5 pr-2 font-medium text-white/70">
              <span className="sr-only">Place</span>
            </th>
            <th scope="col" className="pb-1.5 pr-2 font-medium text-white/70">Bike</th>
            <th scope="col" className="pb-1.5 pr-2 text-right font-medium text-white/70">Quarter mile</th>
            <th scope="col" className="pb-1.5 text-right font-medium text-white/70">Finish speed</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={r.bike_id ?? i} className="border-t border-white/10">
              <td className="py-1.5 pr-2 tabular-nums text-white/60">{i + 1}</td>
              <td className="py-1.5 pr-2 text-white/85">{r.bike_name}</td>
              <td className={`py-1.5 pr-2 text-right font-mono tabular-nums ${i === 0 ? 'text-accent' : 'text-white'}`}>
                {r.finished_quarter === false
                  ? 'Did not finish'
                  : r.et_quarter_s != null
                    ? `${fmtNum(r.et_quarter_s)} s`
                    : ''}
              </td>
              <td className="py-1.5 text-right font-mono tabular-nums text-white/80">
                {r.trap_speed_kmh != null ? `${fmtNum(r.trap_speed_kmh, 0)} km/h` : ''}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {payload.candidates_considered != null && (
        <p className="text-xs text-white/55">
          Shortlisted from {payload.candidates_considered} catalog bikes by power to weight, then each one simulated.
        </p>
      )}
    </div>
  );
}

function OutlawBlock({ payload }) {
  const build = payload.build || {};
  const tire = payload.tire_stage || {};
  const setup = payload.setup || {};
  const extraLines = [];
  if (tire.applied) {
    extraLines.push({
      label: 'Tyre',
      text: `${tire.tire || 'Drag tire'}${tire.mu_peak != null ? ` (μ ${Number(tire.mu_peak).toFixed(2)})` : ''}`,
    });
  } else if (tire.note) {
    extraLines.push({ label: 'Tyre', text: tire.note });
  }
  if (setup.gearing?.recommendation) {
    extraLines.push({ label: 'Gearing', text: setup.gearing.recommendation });
  }
  if (setup.launch_rpm?.recommended_rpm != null) {
    extraLines.push({
      label: 'Launch RPM',
      text: `${Math.round(setup.launch_rpm.recommended_rpm).toLocaleString('en-IN')} rpm`,
    });
  }
  return (
    <BuildSummary
      title={payload.tier_label || 'No-limit build'}
      bikeName={build.bike_name}
      baseEt={payload.baseline_et_s}
      finalEt={payload.final_et_s}
      costInr={payload.total_cost_inr}
      budgetLabel={payload.budget_unlimited ? 'No limit' : fmtINR(payload.budget_inr)}
      parts={build.parts || []}
      extraLines={extraLines}
    />
  );
}

function AutotuneBlock({ payload }) {
  const rows = [];
  if (payload.gearing?.recommendation) {
    rows.push(['Gearing', payload.gearing.recommendation]);
  }
  if (payload.launch_rpm?.recommended_rpm != null) {
    rows.push([
      'Launch RPM',
      `${Math.round(payload.launch_rpm.recommended_rpm).toLocaleString('en-IN')} rpm`,
    ]);
  }
  if (payload.tire_pressure?.rear_psi != null) {
    rows.push([
      'Tyre pressure',
      payload.tire_pressure.front_psi
        ? `rear ${Math.round(payload.tire_pressure.rear_psi)} psi, front ${Math.round(payload.tire_pressure.front_psi)} psi`
        : `rear ${Math.round(payload.tire_pressure.rear_psi)} psi`,
    ]);
  }
  if (payload.fuel_timing?.fuel_trim_pct != null) {
    rows.push([
      'Fuel and timing',
      `${payload.fuel_timing.fuel_trim_pct > 0 ? '+' : ''}${payload.fuel_timing.fuel_trim_pct}% fuel, +${payload.fuel_timing.timing_advance_deg ?? 0}° ignition advance`,
    ]);
  }
  const stockEt = payload.stock?.et_s;
  const combEt = payload.combined?.et_s;
  return (
    <div className="space-y-2 rounded-lg border border-white/10 bg-asphalt-3 p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="flex items-center gap-1.5 text-sm font-medium text-white/85">
          <Timer size={14} className="text-white/60" aria-hidden="true" /> Race-day setup
        </p>
        {stockEt != null && combEt != null && (
          <p className="text-sm tabular-nums text-white/70">
            {fmtNum(stockEt)} s → <span className="font-bold text-accent">{fmtNum(combEt)} s</span>
          </p>
        )}
      </div>
      <div className="space-y-1">
        {rows.map(([label, text]) => (
          <p key={label} className="text-sm text-white/70">
            <span className="mr-2 font-medium text-white/85">{label}</span>
            {text}
          </p>
        ))}
      </div>
    </div>
  );
}

// Only http(s) URLs are safe to put in an href. Citation URLs come from web
// search results relayed through the chat agent, i.e. external + untrusted; a
// `javascript:`/`data:` URI would execute on click (React does not sanitize
// href). Returns the URL if safe, else null.
function safeHttpUrl(u) {
  if (typeof u !== "string") return null;
  try {
    const parsed = new URL(u, "https://motoquant.in");
    return parsed.protocol === "http:" || parsed.protocol === "https:" ? u : null;
  } catch {
    return null;
  }
}

function Citations({ payload }) {
  const results = (payload.results || []).slice(0, 5);
  if (results.length === 0) return null;
  return (
    <div className="space-y-1">
      <p className="text-sm font-medium text-white/70">Sources</p>
      {results.map((r, i) => {
        const href = safeHttpUrl(r.url);
        const label = r.title || r.url || "source";
        const cls =
          "chip max-w-full gap-1.5 text-white/70 hover:text-white hover:border-white/30 transition-colors";
        // Unsafe/blocked scheme → render as inert text, never a live link.
        if (!href) {
          return (
            <span key={i} className={cls}>
              <LinkIcon size={10} className="shrink-0" aria-hidden="true" />
              <span className="truncate">{label}</span>
            </span>
          );
        }
        return (
          <a
            key={i}
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            className={cls}
          >
            <LinkIcon size={10} className="shrink-0" aria-hidden="true" />
            <span className="truncate">{label}</span>
          </a>
        );
      })}
    </div>
  );
}

// Ordered block dispatch. Intermediate lookups (parts/tires/bike_details/
// venues) collapse to one-line chips so the transcript stays readable.
function ChatBlock({ block }) {
  const { type, payload } = block || {};
  if (!payload || payload.error) return null;
  switch (type) {
    case 'sim_result':
      return <SimTiles payload={payload} />;
    case 'estimated_sim':
      return <SimTiles payload={payload} estimated />;
    case 'top_speed':
      return <TopSpeedTiles payload={payload} />;
    case 'compare_result':
      return <CompareBlock payload={payload} />;
    case 'build_result':
      return <BuildBlock payload={payload} />;
    case 'rank_result':
      return <RankBlock payload={payload} />;
    case 'outlaw_result':
      return <OutlawBlock payload={payload} />;
    case 'autotune_result':
      return <AutotuneBlock payload={payload} />;
    case 'web_citations':
      return <Citations payload={payload} />;
    case 'parts':
      return <LookupChip label={`Looked up ${payload.count ?? (payload.parts || []).length} parts`} />;
    case 'tires':
      return <LookupChip label={`Looked up ${payload.count ?? (payload.tires || []).length} tyres`} />;
    case 'venues':
      return <LookupChip label={`Listed ${(payload.venues || []).length} venues`} />;
    case 'bike_details': {
      const name = [payload.manufacturer, payload.model].filter(Boolean).join(' ');
      return <LookupChip label={`Looked up specs: ${name || `bike #${payload.bike_id}`}`} />;
    }
    default:
      return null;
  }
}

// ─── error banners ──────────────────────────────────────────────────────────
function ErrorBanner({ tone = 'red', icon: Icon = AlertCircle, children }) {
  const cls =
    tone === 'amber'
      ? 'bg-signal-stage/10 border-signal-stage/30 text-signal-stage'
      : 'bg-signal-foul/10 border-signal-foul/30 text-signal-foul';
  return (
    <div role="alert" className={`flex items-start gap-2 rounded-lg border p-3 text-sm ${cls}`}>
      <Icon size={14} className="shrink-0 mt-0.5" aria-hidden="true" />
      <span className="min-w-0">{children}</span>
    </div>
  );
}

// ─── assistant choice and the visitor's own key ─────────────────────────────
const KEY_LINE =
  'Your key stays in this browser. It is sent with your questions to answer them and is never stored on our server.';

function AssistantSettings({
  assistant, onAssistant, keyState, onSaveKey, onRemember, onRemoveKey,
  keyOpen, onToggleKey, notice, dailyFreeLimit, keyInputRef,
}) {
  const uid = useId();
  const selectId = `${uid}-assistant`;
  const hintId = `${uid}-assistant-hint`;
  const panelId = `${uid}-key-panel`;
  const inputId = `${uid}-key`;
  const errorId = `${uid}-key-error`;
  const [draft, setDraft] = useState('');
  const [draftRemember, setDraftRemember] = useState(false);
  const [keyError, setKeyError] = useState('');
  const savedKey = keyState.key;
  const remember = savedKey ? keyState.remember : draftRemember;

  function submit(e) {
    e.preventDefault();
    if (!looksLikeAnthropicKey(draft)) {
      setKeyError('That does not look like an Anthropic API key. Keys start with sk-ant-.');
      return;
    }
    onSaveKey(draft, draftRemember);
    setDraft('');
    setKeyError('');
  }

  return (
    <div className="space-y-3 border-t border-white/10 pt-3">
      <div className="sm:max-w-xs">
        <label htmlFor={selectId} className="field-label">Assistant</label>
        <select
          id={selectId}
          value={assistant}
          onChange={(e) => onAssistant(e.target.value)}
          aria-describedby={hintId}
          className="input-base h-11"
        >
          {ASSISTANTS.map((a) => (
            <option key={a.id} value={a.id}>{a.label}</option>
          ))}
        </select>
        <p id={hintId} className="field-hint">{assistantInfo(assistant).description}</p>
      </div>

      <div>
        <button
          type="button"
          onClick={onToggleKey}
          aria-expanded={keyOpen}
          aria-controls={panelId}
          className="inline-flex min-h-[44px] items-center gap-1.5 rounded-md text-sm font-semibold text-accent transition-colors hover:text-accent-bright focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/70"
        >
          <ChevronDown
            size={16}
            aria-hidden="true"
            className={`transition-transform ${keyOpen ? 'rotate-180' : ''}`}
          />
          Use your own key
          {savedKey && <span className="font-normal text-white/60">(in use)</span>}
        </button>

        {keyOpen && (
          <div id={panelId} className="mt-2 space-y-3 rounded-lg border border-white/10 bg-asphalt-3 p-3">
            {notice && <p className="text-sm text-signal-stage">{notice}</p>}

            {savedKey && (
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="text-sm text-white/80">
                  Using your key <span className="font-mono">{maskKey(savedKey)}</span>
                </p>
                <button type="button" onClick={onRemoveKey} className="btn-ghost btn-sm">
                  Remove key
                </button>
              </div>
            )}

            <form onSubmit={submit} className="space-y-1">
              <label htmlFor={inputId} className="field-label">
                {savedKey ? 'Use a different key' : 'Your Anthropic API key'}
              </label>
              <div className="flex gap-2">
                <input
                  ref={keyInputRef}
                  id={inputId}
                  type="password"
                  autoComplete="off"
                  autoCapitalize="off"
                  spellCheck={false}
                  value={draft}
                  onChange={(e) => {
                    setDraft(e.target.value);
                    if (keyError) setKeyError('');
                  }}
                  placeholder="sk-ant-..."
                  aria-invalid={keyError ? true : undefined}
                  aria-describedby={keyError ? errorId : undefined}
                  className="input-base h-11 min-w-0 flex-1 font-mono"
                />
                <button type="submit" disabled={!draft.trim()} className="btn-primary btn-sm shrink-0">
                  Use key
                </button>
              </div>
              {keyError && (
                <p id={errorId} role="alert" className="text-sm text-signal-foul">{keyError}</p>
              )}
            </form>

            <label className="flex min-h-11 cursor-pointer items-center gap-2.5 text-sm text-white/85">
              <input
                type="checkbox"
                checked={remember}
                onChange={(e) =>
                  savedKey ? onRemember(e.target.checked) : setDraftRemember(e.target.checked)
                }
                className="h-5 w-5 accent-accent"
              />
              Remember on this device
            </label>

            <p className="text-sm text-white/75">{KEY_LINE}</p>
            <p className="field-hint">
              {keyState.memoryOnly
                ? 'This browser would not store the key, so it is kept only until you leave this page.'
                : remember
                  ? 'Saved in this browser until you remove it.'
                  : 'Kept for this tab only and cleared when you close it.'}
              {dailyFreeLimit
                ? ` The free assistant allows ${dailyFreeLimit} questions a day, and a question to the doctor counts as two. With your own key that daily limit does not apply.`
                : ''}
            </p>

            <a
              href={CONSOLE_KEYS_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex min-h-[44px] items-center gap-1.5 text-sm text-accent transition-colors hover:text-accent-bright"
            >
              Get a key in the Anthropic Console
              <ExternalLink size={14} aria-hidden="true" />
            </a>
          </div>
        )}
      </div>
    </div>
  );
}

function notifyAssistantChange() {
  try {
    window.dispatchEvent(new Event(ASSISTANT_EVENT));
  } catch {
    /* no window */
  }
}

// ─── main component ─────────────────────────────────────────────────────────
// eslint-disable-next-line no-unused-vars
export default function ChatPanel({ apiUrl }) {
  const [query, setQuery] = useState('');
  // Transcript entries:
  //   {id, role:'user',      content}
  //   {id, role:'assistant', content (summary text), result (ChatResponse)}
  //   {id, role:'assistant', content:'', failed: {text, offerKey}}
  const [turns, setTurns] = useState([]);
  const textareaRef = useRef(null);
  const scrollRef = useRef(null);
  const idRef = useRef(0);
  const reduce = useReducedMotion();

  // ChatPanel only renders in the browser (both mounts use ssr:false), so
  // storage can be read on first render.
  const [assistant, setAssistant] = useState(() => readAssistant(browserStores().local));
  const [keyState, setKeyState] = useState(() => readKey(browserStores()));
  const [keyOpen, setKeyOpen] = useState(false);
  const [serverInfo, setServerInfo] = useState(null);
  const keyInputRef = useRef(null);
  const focusKeyRef = useRef(false);

  // Is the free assistant on? An older or unreachable server gives null, and
  // the chat then reports problems per question instead.
  useEffect(() => {
    const ctrl = new AbortController();
    getAssistantInfo({ signal: ctrl.signal }).then((info) => {
      if (ctrl.signal.aborted || !info) return;
      setServerInfo(info);
      if (!info.freeAvailable) setKeyOpen(true);
    });
    return () => ctrl.abort();
  }, []);

  // Keep both chat mounts (and other tabs) in step with storage.
  useEffect(() => {
    const sync = () => {
      const stores = browserStores();
      setAssistant(readAssistant(stores.local));
      setKeyState((prev) => (prev.memoryOnly ? prev : readKey(stores)));
    };
    window.addEventListener(ASSISTANT_EVENT, sync);
    window.addEventListener('storage', sync);
    return () => {
      window.removeEventListener(ASSISTANT_EVENT, sync);
      window.removeEventListener('storage', sync);
    };
  }, []);

  useEffect(() => {
    if (keyOpen && focusKeyRef.current) {
      focusKeyRef.current = false;
      keyInputRef.current?.focus();
    }
  }, [keyOpen]);

  function openKeyPanel() {
    if (keyOpen) {
      keyInputRef.current?.focus();
    } else {
      focusKeyRef.current = true;
      setKeyOpen(true);
    }
  }

  function chooseAssistant(id) {
    setAssistant(id);
    saveAssistant(browserStores().local, id);
    notifyAssistantChange();
  }

  function handleSaveKey(raw, remember) {
    const stores = browserStores();
    if (saveKey(stores, raw, remember)) {
      setKeyState(readKey(stores));
      notifyAssistantChange();
    } else {
      // Storage is blocked: keep the key for this page only.
      setKeyState({ key: raw.trim(), remember: false, memoryOnly: true });
    }
  }

  function handleRemember(remember) {
    if (!keyState.key || keyState.memoryOnly) return;
    const stores = browserStores();
    if (saveKey(stores, keyState.key, remember)) {
      setKeyState(readKey(stores));
      notifyAssistantChange();
    }
  }

  function handleRemoveKey() {
    removeKey(browserStores());
    setKeyState({ key: '', remember: false });
    notifyAssistantChange();
  }

  // Job-backed chat turn — useAsyncTask owns AbortController + live progress;
  // chatJob cancels the job server-side when the signal aborts (■ Stop).
  // Results/failures are appended to the transcript inside the task fn so
  // every turn keeps its own reply + blocks.
  const task = useAsyncTask(async (signal, onProgress, q, history, asst, apiKey) => {
    try {
      const res = await chatJob(q, history, { signal, onProgress, assistant: asst, apiKey });
      if (!signal.aborted) {
        setTurns((prev) => [
          ...prev,
          { id: idRef.current++, role: 'assistant', content: res?.summary || '', result: res },
        ]);
      }
      return res;
    } catch (e) {
      if (e?.name === 'AbortError') throw e; // Stop / superseded query — quiet
      if (!signal.aborted) {
        setTurns((prev) => [
          ...prev,
          {
            id: idRef.current++,
            role: 'assistant',
            content: '',
            failed: describeChatFailure(e),
          },
        ]);
      }
      return undefined;
    }
  });

  // Auto-resize textarea up to 120px
  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = 'auto';
    ta.style.height = `${Math.min(ta.scrollHeight, 120)}px`;
  }, [query]);

  // Keep the transcript pinned to the newest turn (scrolls the container
  // only — never the page; instant assignment is reduced-motion-safe).
  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [turns, task.active]);

  function send(text) {
    const q = (text ?? query).trim();
    if (!q) return;
    // History = prior turns with real content (failed turns excluded),
    // capped to the last HISTORY_TURNS. Built BEFORE appending the new
    // user turn — the server gets {messages: history, query: q}.
    const history = turns
      .filter((t) => !t.failed && t.content)
      .map((t) => ({ role: t.role, content: t.content }))
      .slice(-HISTORY_TURNS);
    setTurns((prev) => [...prev, { id: idRef.current++, role: 'user', content: q }]);
    setQuery('');
    // A new query supersedes an in-flight one (useAsyncTask aborts it,
    // which also cancels the old job server-side).
    task.run(q, history, assistant, keyState.key);
  }

  function newChat() {
    task.stop();
    task.reset();
    setTurns([]);
    setQuery('');
    textareaRef.current?.focus();
  }

  function onKeyDown(e) {
    // Enter submits; Shift+Enter inserts a newline (standard chat UX).
    if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
      e.preventDefault();
      send();
    }
  }

  function keyAction() {
    return (
      <button
        type="button"
        onClick={openKeyPanel}
        className="mt-1 flex min-h-[44px] items-center gap-1.5 font-semibold underline underline-offset-2"
      >
        <KeyRound size={14} aria-hidden="true" />
        {keyState.key ? 'Change your key' : 'Add your own key'}
      </button>
    );
  }

  // Renders one assistant turn: error branches → blocks → summary prose.
  function renderAssistant(turn) {
    if (turn.failed) {
      const f = typeof turn.failed === 'string' ? { text: turn.failed } : turn.failed;
      return (
        <ErrorBanner tone={f.offerKey ? 'amber' : 'red'}>
          {f.text}
          {f.offerKey && keyAction()}
        </ErrorBanner>
      );
    }
    const r = turn.result || {};
    const err = r.error;

    const copy = err ? chatErrorCopy(err, { ownKey: r.own_key === true }) : null;
    if (copy) {
      const showDetail = r.error_detail && (err === 'agent_failed' || err === 'key_rejected');
      return (
        <ErrorBanner tone={copy.tone} icon={copy.offerKey ? KeyRound : AlertCircle}>
          {copy.text}
          {showDetail && <span className="mt-1 block opacity-80">{r.error_detail}</span>}
          {copy.offerKey && keyAction()}
        </ErrorBanner>
      );
    }

    if (err === 'bike_not_found') {
      return (
        <div className="space-y-2">
          <p className="text-sm text-white/70">
            We couldn&apos;t find a bike matching &quot;{r.raw_query}&quot;.
            {r.error_detail ? ` ${r.error_detail}` : ''}
          </p>
          {r.bike_suggestions?.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              <p className="w-full text-sm text-white/60">Did you mean:</p>
              {r.bike_suggestions.map((s, i) => (
                <button
                  key={s.id ?? i}
                  type="button"
                  onClick={() => {
                    setQuery([s.manufacturer, s.model, s.year_range].filter(Boolean).join(' '));
                    textareaRef.current?.focus();
                  }}
                  className="min-h-[44px] rounded-lg border border-white/10 bg-asphalt-3 px-3 py-1.5 text-left text-sm text-white/80 transition-colors hover:border-white/30 hover:text-white"
                >
                  {[s.manufacturer, s.model, s.year_range].filter(Boolean).join(' ')}
                </button>
              ))}
            </div>
          )}
        </div>
      );
    }

    if (err) {
      // Catch-all: parse_failed / sim_failed / anything new.
      return (
        <ErrorBanner>
          {r.error_detail || `The request could not be completed (${err}).`}
        </ErrorBanner>
      );
    }

    // Success — reply text, then that turn's blocks underneath. Older/classic
    // backends return no blocks[] but do return sim_result — keep the tiles.
    const blocks =
      Array.isArray(r.blocks) && r.blocks.length > 0
        ? r.blocks
        : r.sim_result
          ? [{ type: 'sim_result', payload: r.sim_result }]
          : [];
    // Group consecutive lookup chips onto one row.
    const chipTypes = new Set(['parts', 'tires', 'venues', 'bike_details']);
    const chips = blocks.filter((b) => chipTypes.has(b.type));
    const rich = blocks.filter((b) => !chipTypes.has(b.type));

    return (
      <div className="space-y-3">
        {turn.content && (
          <p className="whitespace-pre-wrap text-base leading-relaxed text-white/85">
            {turn.content}
          </p>
        )}
        {rich.map((b, i) => (
          <ChatBlock key={i} block={b} />
        ))}
        {chips.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {chips.map((b, i) => (
              <ChatBlock key={i} block={b} />
            ))}
          </div>
        )}
        {(r.assistant === 'doctor' || r.assistant === 'mechanic') && (
          <p className="text-xs text-white/55">
            {assistantInfo(r.assistant).name} answered{r.own_key ? ', using your key' : ''}.
          </p>
        )}
      </div>
    );
  }

  const freeOff = serverInfo != null && !serverInfo.freeAvailable;
  const notice = freeOff
    ? keyState.key
      ? 'The free assistant is not available right now, so your questions use your key.'
      : 'The free assistant is not available right now. Add your own Anthropic key to ask questions.'
    : '';

  return (
    <div className="space-y-4">
      {/* Transcript */}
      {turns.length > 0 && (
        <div
          ref={scrollRef}
          role="log"
          aria-live="polite"
          aria-label="Chat transcript"
          tabIndex={0}
          className="max-h-[30rem] space-y-4 overflow-y-auto pr-1"
        >
          {turns.map((turn) =>
            turn.role === 'user' ? (
              <div key={turn.id} className="flex justify-end">
                <div className="max-w-[85%] whitespace-pre-wrap rounded-xl rounded-br-sm border border-white/10 bg-accent/10 px-3.5 py-2 text-base text-white">
                  {turn.content}
                </div>
              </div>
            ) : (
              <motion.div
                key={turn.id}
                className="card p-3.5"
                initial={{ opacity: 0, y: reduce ? 0 : 6 }}
                animate={{ opacity: 1, y: 0 }}
              >
                {renderAssistant(turn)}
              </motion.div>
            )
          )}
        </div>
      )}

      {/* Live progress — real stage text from the job poller + ■ Stop */}
      {task.active && (
        <SimProgress
          active
          progress={task.progress}
          stage={task.stage}
          label="Working on it"
          onStop={task.stop}
        />
      )}

      {/* Input — stays enabled while loading so a new query supersedes the old */}
      <div className="flex items-end gap-2">
        <label htmlFor="chat-message" className="sr-only">Ask a question</label>
        <textarea
          id="chat-message"
          ref={textareaRef}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={onKeyDown}
          rows={2}
          placeholder='Ask anything, e.g. "How fast is a Duke 390 at Aamby Valley?"'
          className="input-base h-auto min-h-[3rem] flex-1 resize-none py-3"
        />
        <motion.button
          onClick={() => send()}
          disabled={!query.trim()}
          whileHover={reduce ? undefined : { scale: 1.05 }}
          whileTap={reduce ? undefined : { scale: 0.95 }}
          className="btn-primary w-12 shrink-0 px-0 disabled:cursor-not-allowed disabled:opacity-40"
          aria-label="Send question"
        >
          <Send size={18} />
        </motion.button>
      </div>

      <div className="flex items-center justify-between gap-3">
        <p className="text-sm text-white/60">
          Press Enter to send, Shift+Enter for a new line.
        </p>
        {turns.length > 0 && (
          <button
            type="button"
            onClick={newChat}
            className="flex min-h-[44px] items-center gap-1.5 px-2 text-sm text-white/70 transition-colors hover:text-white"
          >
            <RotateCcw size={14} aria-hidden="true" /> New chat
          </button>
        )}
      </div>

      {/* Example chips — shown before the first turn */}
      {turns.length === 0 && !task.active && (
        <div className="flex flex-wrap gap-1.5">
          {CHAT_EXAMPLES.map((ex) => (
            <button
              key={ex}
              type="button"
              onClick={() => {
                setQuery(ex);
                textareaRef.current?.focus();
              }}
              className="min-h-[44px] rounded-lg border border-white/10 bg-asphalt-3 px-3 py-2 text-left text-sm text-white/80 transition-colors hover:border-white/30 hover:text-white"
            >
              {ex}
            </button>
          ))}
        </div>
      )}

      <AssistantSettings
        assistant={assistant}
        onAssistant={chooseAssistant}
        keyState={keyState}
        onSaveKey={handleSaveKey}
        onRemember={handleRemember}
        onRemoveKey={handleRemoveKey}
        keyOpen={keyOpen}
        onToggleKey={() => setKeyOpen((o) => !o)}
        notice={notice}
        dailyFreeLimit={serverInfo?.freeAvailable ? serverInfo.dailyFreeLimit : null}
        keyInputRef={keyInputRef}
      />
    </div>
  );
}
