'use client';

// ChatPanel — natural-language query input + result display for the
// /api/chat endpoint.  Self-contained; takes apiUrl as a prop so it can
// be reused by both the landing-page SimulatorWidget and the full
// /simulator page.
//
// Server error cases handled inline (matches Phase A backend contract):
//   • bike_not_found        → clickable suggestion chips
//   • llm_not_configured    → ANTHROPIC_API_KEY setup banner
//   • parse_failed          → inline error with detail
//   • sim_failed            → inline error with detail
//
// Cockpit v3: spinner replaced by a staged SimProgress ("Thinking…") above
// the response skeleton, and queries are abortable — submitting a new query
// cancels the in-flight one instead of racing it.

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertCircle, Send, KeyRound } from 'lucide-react';
import SimProgress from './SimProgress';
import { Skeleton } from './Skeleton';

const CHAT_EXAMPLES = [
  'How fast is a KTM RC 390 at Aamby Valley?',
  'What ET does an R15 V4 run in 38°C heat?',
  'Compare Hayabusa vs Ninja H2',
];

export default function ChatPanel({ apiUrl }) {
  const [query, setQuery] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [chatResult, setChatResult] = useState(null);
  const [chatError, setChatError] = useState(null);
  const textareaRef = useRef(null);
  const abortRef = useRef(null);

  // Auto-resize textarea up to 120px
  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = 'auto';
    ta.style.height = `${Math.min(ta.scrollHeight, 120)}px`;
  }, [query]);

  // Abort any in-flight query on unmount.
  useEffect(() => () => abortRef.current?.abort(), []);

  async function runChat() {
    const q = query.trim();
    if (!q) return;
    // A new query cancels the old one — no racing responses.
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    setChatLoading(true);
    setChatResult(null);
    setChatError(null);
    try {
      const res = await fetch(`${apiUrl}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: q, run_summary: true }),
        signal: controller.signal,
      });
      if (!res.ok) {
        const msg = await res.text();
        throw new Error(`Server error ${res.status}: ${msg}`);
      }
      const data = await res.json();
      if (!controller.signal.aborted) setChatResult(data);
    } catch (e) {
      if (e?.name !== 'AbortError') setChatError(e.message);
    } finally {
      // Only the newest request may clear the loading flag.
      if (abortRef.current === controller) setChatLoading(false);
    }
  }

  function onKeyDown(e) {
    // Enter submits; Shift+Enter inserts a newline (standard chat UX).
    if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
      e.preventDefault();
      runChat();
    }
  }

  // Derived result fields
  const r = chatResult;
  const et = r?.sim_result?.et_quarter_s;
  const trap = r?.sim_result?.trap_speed_kmh;
  const et60 = r?.sim_result?.et_60ft_s;
  const etEighth = r?.sim_result?.et_eighth_s;

  return (
    <div className="space-y-4">
      {/* Input — stays enabled while loading so a new query can cancel the old */}
      <div className="flex gap-2 items-end">
        <textarea
          ref={textareaRef}
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={onKeyDown}
          rows={2}
          placeholder="e.g. How fast is an R15 V4 in 38°C at Aamby Valley?"
          className="input-base flex-1 h-auto min-h-[2.75rem] resize-none py-2.5 text-sm bg-ink-1"
        />
        <motion.button
          onClick={runChat}
          disabled={!query.trim()}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="shrink-0 p-2.5 rounded-md bg-brand-orange hover:bg-brand-orangeLight disabled:opacity-40 disabled:cursor-not-allowed text-black flex items-center justify-center"
          aria-label="Send chat query"
        >
          <Send size={18} />
        </motion.button>
      </div>

      <p className="font-mono text-[10px] text-white/30">
        Enter to submit · Shift+Enter for newline
      </p>

      {/* Example chips — shown before first query */}
      {!chatResult && !chatLoading && !chatError && (
        <div className="flex flex-wrap gap-1.5">
          {CHAT_EXAMPLES.map(ex => (
            <button
              key={ex}
              onClick={() => { setQuery(ex); textareaRef.current?.focus(); }}
              className="text-[11px] px-2.5 py-1 rounded-full bg-white/[0.04] text-white/50 border border-white/10 hover:text-white/80 hover:border-white/20 transition-colors"
            >
              {ex}
            </button>
          ))}
        </div>
      )}

      {/* Network error */}
      {chatError && (
        <div className="flex gap-2 items-start p-3 rounded-lg bg-brand-red/10 border border-brand-red/30 text-brand-red text-xs">
          <AlertCircle size={14} className="shrink-0 mt-0.5" />
          {chatError}
        </div>
      )}

      {/* Loading — staged progress bar (cold-start caption after 4 s) above
          a response-shaped skeleton. Reduced-motion-safe via .skeleton +
          SimProgress internals. */}
      {chatLoading && (
        <div className="space-y-3">
          <SimProgress active label="Thinking" />
          <Skeleton className="h-3 w-full" />
          <Skeleton className="h-3 w-5/6" />
          <div className="grid grid-cols-2 gap-3 mt-4">
            {[0, 1].map(i => (
              <div key={i} className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4 space-y-2">
                <Skeleton className="h-2.5 w-16" />
                <Skeleton className="h-8 w-24" />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Result */}
      <AnimatePresence>
        {chatResult && !chatLoading && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="space-y-4"
          >
            {/* llm_not_configured */}
            {chatResult.error === 'llm_not_configured' && (
              <div className="flex gap-2 items-start p-3 rounded-lg bg-brand-amber/10 border border-brand-amber/30 text-brand-amber text-xs">
                <KeyRound size={14} className="shrink-0 mt-0.5" />
                <span>
                  Natural-language chat is offline — server is missing an LLM API key.
                  {chatResult.error_detail && (
                    <span className="block mt-1 opacity-70 font-mono">
                      {chatResult.error_detail}
                    </span>
                  )}
                </span>
              </div>
            )}

            {/* bike_not_found */}
            {chatResult.error === 'bike_not_found' && (
              <div className="space-y-2">
                <p className="text-xs text-white/50">
                  Couldn't match a bike for "{chatResult.raw_query}".
                  {chatResult.error_detail ? ` ${chatResult.error_detail}` : ''}
                </p>
                {chatResult.bike_suggestions?.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    <p className="w-full text-[11px] text-white/40">Did you mean:</p>
                    {chatResult.bike_suggestions.map((s, i) => (
                      <button
                        key={s.id ?? i}
                        onClick={() => setQuery([s.manufacturer, s.model, s.year_range].filter(Boolean).join(' '))}
                        className="text-[11px] px-2.5 py-1 rounded-full bg-white/[0.06] text-white/70 border border-white/10 hover:border-brand-orange/50 hover:text-white transition-colors"
                      >
                        {[s.manufacturer, s.model, s.year_range].filter(Boolean).join(' ')}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* parse_failed / sim_failed */}
            {(chatResult.error === 'parse_failed' || chatResult.error === 'sim_failed') && (
              <div className="flex gap-2 items-start p-3 rounded-lg bg-brand-red/10 border border-brand-red/30 text-brand-red text-xs">
                <AlertCircle size={14} className="shrink-0 mt-0.5" />
                {chatResult.error_detail || 'The simulation could not be completed.'}
              </div>
            )}

            {/* Success — sim tiles */}
            {!chatResult.error && chatResult.sim_result && (
              <div className="space-y-3">
                {chatResult.bike_name && (
                  <p className="text-xs text-white/50 font-medium">{chatResult.bike_name}</p>
                )}
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { label: 'Quarter-mile ET', value: et != null ? `${et.toFixed(3)} s` : '—', accent: true },
                    { label: 'Trap speed', value: trap != null ? `${trap.toFixed(1)} km/h` : '—', accent: false },
                    { label: '60 ft', value: et60 != null ? `${et60.toFixed(3)} s` : '—', accent: false },
                    { label: '⅛ mile', value: etEighth != null ? `${etEighth.toFixed(3)} s` : '—', accent: false },
                  ].map(({ label, value, accent }) => (
                    <motion.div
                      key={label}
                      initial={{ scale: 0.95, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-3 text-center"
                    >
                      <p className="label-mono mb-1">{label}</p>
                      <p className={`text-xl font-mono font-bold ${accent ? 'text-brand-orange' : 'text-white'}`}>
                        {value}
                      </p>
                    </motion.div>
                  ))}
                </div>
              </div>
            )}

            {/* Summary prose */}
            {!chatResult.error && chatResult.summary && (
              <p className="text-xs text-white/60 leading-relaxed border-l-2 border-brand-orange/40 pl-3">
                {chatResult.summary}
              </p>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
