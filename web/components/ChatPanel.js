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
//   • Error branches: llm_not_configured (GROQ_API_KEY / LLM_PROVIDER),
//     bike_not_found (suggestion chips), rate_limited, and a CATCH-ALL that
//     surfaces error_detail (previously unknown errors rendered nothing).

import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion, useReducedMotion } from 'framer-motion';
import {
  AlertCircle, Send, KeyRound, RotateCcw, Timer, Link as LinkIcon, Lock,
} from 'lucide-react';
import SimProgress from './SimProgress';
import { chatJob, partLabel } from '../lib/api';
import useAsyncTask from '../lib/useAsyncTask';

const CHAT_EXAMPLES = [
  'Best possible outlaw build for a Hayabusa',
  'Compare ZX-10R vs S1000RR at Aamby Valley',
  'How fast is a 2025 Kove 450RR?',
];

// How many prior turns ride along with each request (server caps at 24).
const HISTORY_TURNS = 12;

// ─── formatting helpers ─────────────────────────────────────────────────────
const fmtNum = (v, d = 3) => (v == null ? '—' : Number(v).toFixed(d));
const fmtINR = (n) =>
  n == null ? '—' : `₹${Math.round(n).toLocaleString('en-IN')}`;

// ─── shared tile ────────────────────────────────────────────────────────────
function Tile({ label, value, accent = false }) {
  return (
    <div className="rounded-lg border border-white/[0.06] bg-white/[0.02] p-3 text-center">
      <p className="label-mono mb-1">{label}</p>
      <p className={`text-xl font-mono font-bold tabular-nums ${accent ? 'text-accent' : 'text-white'}`}>
        {value}
      </p>
    </div>
  );
}

function LookupChip({ label }) {
  return (
    <span className="chip normal-case tracking-normal text-white/50">
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
            <p className="text-xs text-white/50 font-medium">{payload.bike_name}</p>
          )}
          {estimated && (
            <span className="chip chip-stage font-bold">
              Estimated{conf != null ? ` — confidence ${conf}%` : ''}
            </span>
          )}
        </div>
      )}
      <div className="grid grid-cols-2 gap-3">
        <Tile label="Quarter-mile ET" value={payload.et_quarter_s != null ? `${fmtNum(payload.et_quarter_s)} s` : '—'} accent />
        <Tile label="Trap speed" value={payload.trap_speed_kmh != null ? `${fmtNum(payload.trap_speed_kmh, 1)} km/h` : '—'} />
        <Tile label="60 ft" value={payload.et_60ft_s != null ? `${fmtNum(payload.et_60ft_s)} s` : '—'} />
        <Tile label="⅛ mile" value={payload.et_eighth_s != null ? `${fmtNum(payload.et_eighth_s)} s` : '—'} />
      </div>
      {estimated && payload.top_speed_kmh != null && (
        <p className="text-[11px] font-mono text-white/40">
          Top speed ~{fmtNum(payload.top_speed_kmh, 1)} km/h
        </p>
      )}
      {Array.isArray(payload.modifications) && payload.modifications.length > 0 && (
        <p className="text-[10px] font-mono text-white/35">
          {payload.modifications.join(' · ')}
        </p>
      )}
      {estimated && assumptions.length > 0 && (
        <ul className="text-[11px] text-white/40 space-y-0.5 list-disc list-inside">
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
        <p className="text-xs text-white/50 font-medium">{payload.bike_name}</p>
      )}
      <div className="grid grid-cols-3 gap-3">
        <Tile label="Top speed" value={payload.top_speed_kmh != null ? `${fmtNum(payload.top_speed_kmh, 1)}` : '—'} accent />
        <Tile label="Gear" value={payload.terminal_gear ?? '—'} />
        <Tile label="RPM" value={payload.terminal_rpm != null ? Math.round(payload.terminal_rpm).toLocaleString('en-IN') : '—'} />
      </div>
      <p className="text-[10px] font-mono text-white/35">
        km/h
        {payload.reached_plateau === false ? ' · did not plateau within the sim window' : ''}
      </p>
    </div>
  );
}

function CompareBlock({ payload }) {
  const a = payload.bike_a || {};
  const b = payload.bike_b || {};
  const delta = payload.delta_et_s;
  const rows = [
    ['ET', (v) => (v?.et_quarter_s != null ? `${fmtNum(v.et_quarter_s)} s` : '—')],
    ['Trap', (v) => (v?.trap_speed_kmh != null ? `${fmtNum(v.trap_speed_kmh, 1)} km/h` : '—')],
    ['60 ft', (v) => (v?.et_60ft_s != null ? `${fmtNum(v.et_60ft_s)} s` : '—')],
  ];
  const aWins = payload.winner && payload.winner === a.bike_name;
  return (
    <div className="rounded-lg border border-white/[0.06] bg-white/[0.02] p-3 space-y-2 overflow-x-auto">
      {payload.winner && (
        <p className="text-xs font-mono text-signal-go">
          {payload.winner} wins{delta != null ? ` by ${Math.abs(delta).toFixed(3)} s` : ''}
        </p>
      )}
      <table className="w-full text-xs">
        <thead>
          <tr className="text-left">
            <th className="label-mono font-medium pb-1.5 pr-2" scope="col">
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
            <tr key={label} className="border-t border-white/[0.05]">
              <td className="label-mono py-1.5 pr-2">{label}</td>
              <td className="py-1.5 pr-2 font-mono text-white tabular-nums">{get(a)}</td>
              <td className="py-1.5 font-mono text-white tabular-nums">{get(b)}</td>
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
    <div className="rounded-lg border border-white/[0.06] bg-white/[0.02] p-3 space-y-3">
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <p className="text-xs font-medium text-white/70">
          {title}
          {bikeName ? <span className="text-white/45"> · {bikeName}</span> : null}
        </p>
        <p className="text-[10px] font-mono text-white/40">
          Budget: <span className="text-white/70">{budgetLabel}</span>
        </p>
      </div>

      <div className="flex items-baseline gap-2 flex-wrap">
        <span className="font-mono text-white/50 text-sm tabular-nums">{fmtNum(baseEt)} s</span>
        <span className="text-white/30 text-xs" aria-hidden="true">→</span>
        <span className="font-mono font-bold text-accent text-xl tabular-nums">{fmtNum(finalEt)} s</span>
        {diff != null && (
          <span className={`font-mono text-xs tabular-nums ${diff < 0 ? 'text-signal-go' : diff > 0 ? 'text-signal-foul' : 'text-white/50'}`}>
            {diff > 0 ? '+' : ''}{diff.toFixed(3)} s
          </span>
        )}
        {costInr != null && (
          <span className="font-mono text-xs text-white/50 tabular-nums ml-auto">{fmtINR(costInr)}</span>
        )}
      </div>

      {Array.isArray(extraLines) && extraLines.length > 0 && (
        <div className="space-y-1">
          {extraLines.map((line, i) => (
            <p key={i} className="text-[11px] text-white/50">
              <span className="label-mono mr-2">{line.label}</span>
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
              className="flex items-center justify-between gap-3 px-2.5 py-1.5 rounded-lg bg-white/[0.03] border border-white/[0.06]"
            >
              <p className="text-xs text-white/80 truncate min-w-0">{partLabel(p.brand, p.name)}</p>
              <p className="text-[11px] font-mono text-white/50 tabular-nums shrink-0">
                {fmtINR(p.price_inr)}
                {p.delta_et_s != null && (
                  /* delta_et_s = with-part − without (July 6, 2026 unified
                     convention): negative = faster = highlight. */
                  <span className={`ml-2 ${Number(p.delta_et_s) < 0 ? 'text-signal-go' : 'text-white/40'}`}>
                    Δ {fmtNum(p.delta_et_s)} s
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

function BuildBlock({ payload }) {
  const noLimit =
    payload.budget_unlimited === true || Number(payload.budget_inr) >= 5_000_000;
  return (
    <BuildSummary
      title={payload.tier_label || 'Build optimizer'}
      bikeName={payload.bike_name}
      baseEt={payload.base_et_s}
      finalEt={payload.optimized_et_s}
      costInr={payload.total_cost_inr}
      budgetLabel={noLimit ? 'No limit' : fmtINR(payload.budget_inr)}
      parts={payload.parts || []}
    />
  );
}

function OutlawBlock({ payload }) {
  const build = payload.build || {};
  const tire = payload.tire_stage || {};
  const setup = payload.setup || {};
  const extraLines = [];
  if (tire.applied) {
    extraLines.push({
      label: 'Rubber',
      text: `${tire.tire || 'Drag tire'}${tire.mu_peak != null ? ` (μ ${Number(tire.mu_peak).toFixed(2)})` : ''}`,
    });
  } else if (tire.note) {
    extraLines.push({ label: 'Rubber', text: tire.note });
  }
  if (setup.gearing?.recommendation) {
    extraLines.push({ label: 'Gearing', text: setup.gearing.recommendation });
  }
  if (setup.launch_rpm?.recommended_rpm != null) {
    extraLines.push({
      label: 'Launch',
      text: `${Math.round(setup.launch_rpm.recommended_rpm).toLocaleString('en-IN')} rpm`,
    });
  }
  return (
    <BuildSummary
      title={payload.tier_label || 'Outlaw build'}
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
      'Launch',
      `${Math.round(payload.launch_rpm.recommended_rpm).toLocaleString('en-IN')} rpm`,
    ]);
  }
  if (payload.tire_pressure?.rear_psi != null) {
    rows.push([
      'Tires',
      `rear ${Math.round(payload.tire_pressure.rear_psi)} psi / front ${Math.round(payload.tire_pressure.front_psi ?? 0) || '—'} psi`,
    ]);
  }
  if (payload.fuel_timing?.fuel_trim_pct != null) {
    rows.push([
      'Fuel',
      `${payload.fuel_timing.fuel_trim_pct > 0 ? '+' : ''}${payload.fuel_timing.fuel_trim_pct}% trim · +${payload.fuel_timing.timing_advance_deg ?? 0}° timing`,
    ]);
  }
  const stockEt = payload.stock?.et_s;
  const combEt = payload.combined?.et_s;
  return (
    <div className="rounded-lg border border-white/[0.06] bg-white/[0.02] p-3 space-y-2">
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <p className="text-xs font-medium text-white/70 flex items-center gap-1.5">
          <Timer size={12} className="text-white/40" aria-hidden="true" /> Setup autotune
        </p>
        {stockEt != null && combEt != null && (
          <p className="font-mono text-xs tabular-nums text-white/60">
            {fmtNum(stockEt)} s → <span className="text-accent font-bold">{fmtNum(combEt)} s</span>
          </p>
        )}
      </div>
      <div className="space-y-1">
        {rows.map(([label, text]) => (
          <p key={label} className="text-[11px] text-white/50">
            <span className="label-mono mr-2">{label}</span>
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
      <p className="label-mono">Sources</p>
      {results.map((r, i) => {
        const href = safeHttpUrl(r.url);
        const label = r.title || r.url || "source";
        const cls =
          "chip normal-case tracking-normal max-w-full gap-1.5 text-white/60 hover:text-white hover:border-white/30 transition-colors";
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
    case 'outlaw_result':
      return <OutlawBlock payload={payload} />;
    case 'autotune_result':
      return <AutotuneBlock payload={payload} />;
    case 'web_citations':
      return <Citations payload={payload} />;
    case 'parts':
      return <LookupChip label={`${payload.count ?? (payload.parts || []).length} parts looked up`} />;
    case 'tires':
      return <LookupChip label={`${payload.count ?? (payload.tires || []).length} tires looked up`} />;
    case 'venues':
      return <LookupChip label={`${(payload.venues || []).length} venues listed`} />;
    case 'bike_details': {
      const name = [payload.manufacturer, payload.model].filter(Boolean).join(' ');
      return <LookupChip label={`Specs: ${name || `bike #${payload.bike_id}`}`} />;
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
    <div className={`flex gap-2 items-start p-3 rounded-lg border text-xs ${cls}`}>
      <Icon size={14} className="shrink-0 mt-0.5" aria-hidden="true" />
      <span className="min-w-0">{children}</span>
    </div>
  );
}

// ─── main component ─────────────────────────────────────────────────────────
// eslint-disable-next-line no-unused-vars
export default function ChatPanel({ apiUrl }) {
  const [query, setQuery] = useState('');
  // Transcript entries:
  //   {id, role:'user',      content}
  //   {id, role:'assistant', content (summary text), result (ChatResponse)}
  //   {id, role:'assistant', content:'', failed: <network error message>}
  const [turns, setTurns] = useState([]);
  const textareaRef = useRef(null);
  const scrollRef = useRef(null);
  const idRef = useRef(0);
  const reduce = useReducedMotion();
  const pathname = usePathname(); // for the 401 sign-in ?next= return path

  // Job-backed chat turn — useAsyncTask owns AbortController + live progress;
  // chatJob cancels the job server-side when the signal aborts (■ Stop).
  // Results/failures are appended to the transcript inside the task fn so
  // every turn keeps its own reply + blocks.
  const task = useAsyncTask(async (signal, onProgress, q, history) => {
    try {
      const res = await chatJob(q, history, { signal, onProgress });
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
            failed: e?.message || 'Request failed — please try again',
            // Structured billing/auth fields off ApiRequestError (lib/api) so
            // the banner can offer an upgrade / sign-in link for 402/401.
            failedStatus: e?.status ?? null,
            failedUpgradeUrl: e?.upgradeUrl ?? null,
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
    task.run(q, history);
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

  // Renders one assistant turn: error branches → blocks → summary prose.
  function renderAssistant(turn) {
    if (turn.failed) {
      // 402 (upgrade / quota) and 401 (sign in) get an actionable link —
      // status + upgrade URL ride on the turn from the ApiRequestError.
      if (turn.failedStatus === 402 || turn.failedStatus === 401) {
        let href = `/login?next=${encodeURIComponent(pathname || '/')}`;
        let cta = 'Sign in';
        if (turn.failedStatus === 402) {
          href = '/pricing';
          cta = 'Upgrade to Pro';
          if (turn.failedUpgradeUrl) {
            try {
              href = new URL(turn.failedUpgradeUrl, 'https://motoquant.in').pathname || '/pricing';
            } catch {
              /* malformed URL → keep /pricing */
            }
          }
        }
        return (
          <ErrorBanner tone="amber" icon={Lock}>
            {turn.failed}{' '}
            <Link href={href} className="font-semibold underline underline-offset-2 hover:opacity-80">
              {cta}
            </Link>
          </ErrorBanner>
        );
      }
      return <ErrorBanner>{turn.failed}</ErrorBanner>;
    }
    const r = turn.result || {};
    const err = r.error;

    if (err === 'llm_not_configured') {
      return (
        <ErrorBanner tone="amber" icon={KeyRound}>
          Natural-language chat is offline — the server has no LLM provider key
          configured. Set <code className="font-mono">GROQ_API_KEY</code> (or the
          key for the provider selected via{' '}
          <code className="font-mono">LLM_PROVIDER</code>).
          {r.error_detail && (
            <span className="block mt-1 opacity-70 font-mono">{r.error_detail}</span>
          )}
        </ErrorBanner>
      );
    }

    if (err === 'rate_limited') {
      return (
        <ErrorBanner tone="amber">
          The engine&apos;s AI is rate-limited right now — try again in a minute.
          {r.error_detail && (
            <span className="block mt-1 opacity-70 font-mono">{r.error_detail}</span>
          )}
        </ErrorBanner>
      );
    }

    if (err === 'bike_not_found') {
      return (
        <div className="space-y-2">
          <p className="text-xs text-white/50">
            Couldn&apos;t match a bike for &quot;{r.raw_query}&quot;.
            {r.error_detail ? ` ${r.error_detail}` : ''}
          </p>
          {r.bike_suggestions?.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              <p className="w-full text-[11px] text-white/40">Did you mean:</p>
              {r.bike_suggestions.map((s, i) => (
                <button
                  key={s.id ?? i}
                  type="button"
                  onClick={() => {
                    setQuery([s.manufacturer, s.model, s.year_range].filter(Boolean).join(' '));
                    textareaRef.current?.focus();
                  }}
                  className="font-mono text-[11px] px-2.5 py-1 rounded bg-white/[0.06] text-white/70 border border-white/10 hover:border-white/30 hover:text-white transition-colors"
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
      // Catch-all: parse_failed / sim_failed / agent_failed / anything new.
      // (The old panel rendered NOTHING for unknown errors — known bug.)
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
          <p className="text-sm text-white/70 leading-relaxed whitespace-pre-wrap">
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
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Transcript */}
      {turns.length > 0 && (
        <div
          ref={scrollRef}
          role="log"
          aria-live="polite"
          aria-label="Chat transcript"
          className="space-y-4 max-h-[30rem] overflow-y-auto pr-1"
        >
          {turns.map((turn) =>
            turn.role === 'user' ? (
              <div key={turn.id} className="flex justify-end">
                <div className="max-w-[85%] rounded-xl rounded-br-sm bg-asphalt-3 border border-white/[0.08] px-3.5 py-2 text-sm text-white/90 whitespace-pre-wrap">
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
          label="Thinking"
          onStop={task.stop}
        />
      )}

      {/* Input — stays enabled while loading so a new query supersedes the old */}
      <div className="flex gap-2 items-end">
        <textarea
          ref={textareaRef}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={onKeyDown}
          rows={2}
          aria-label="Chat message"
          placeholder='Ask anything — sims, compares, builds… e.g. "Best outlaw build for a Hayabusa"'
          className="input-base flex-1 h-auto min-h-[2.75rem] resize-none py-2.5 text-sm"
        />
        <motion.button
          onClick={() => send()}
          disabled={!query.trim()}
          whileHover={reduce ? undefined : { scale: 1.05 }}
          whileTap={reduce ? undefined : { scale: 0.95 }}
          className="btn-primary shrink-0 w-11 px-0 disabled:opacity-40 disabled:cursor-not-allowed"
          aria-label="Send chat query"
        >
          <Send size={18} />
        </motion.button>
      </div>

      <div className="flex items-center justify-between gap-3">
        <p className="font-mono text-[10px] text-white/30">
          Enter to submit · Shift+Enter for newline
        </p>
        {turns.length > 0 && (
          <button
            type="button"
            onClick={newChat}
            className="flex items-center gap-1 font-mono text-[10px] text-white/40 hover:text-white/80 transition-colors"
          >
            <RotateCcw size={10} aria-hidden="true" /> New chat
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
              className="font-mono text-[11px] px-2.5 py-1.5 rounded bg-white/[0.04] text-white/55 border border-white/10 hover:text-white/85 hover:border-white/25 transition-colors"
            >
              {ex}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
