// ChatBox — natural-language query input + result display for the Chat tab
// on SimulatePage.  Calls POST /api/chat via the useChat() hook and handles
// all four error cases the server can return:
//   • bike_not_found        → clickable suggestion chips
//   • llm_not_configured    → banner asking operator to set the provider key
//     (GROQ_API_KEY by default; provider selected via LLM_PROVIDER)
//   • parse_failed          → inline error with detail
//   • sim_failed            → inline error with detail
//
// The `onSuggestionClick` prop lets the parent (SimulatePage) wire the chips
// to the BikePicker so the user can run a normal sim without retyping.

import { useRef, useState, useCallback, useEffect } from "react";
import {
  Send,
  Loader2,
  AlertTriangle,
  KeyRound,
  Bike,
  Zap,
} from "lucide-react";
import { useChat } from "@/hooks/useChat";
import { Skeleton } from "@/components/Skeleton";
import type { ChatBikeSuggestion, ChatResponse } from "@/types/api";

// ─── Skeleton shown while waiting ────────────────────────────────────────────

function ChatSkeleton() {
  return (
    <div className="space-y-4 animate-pulse" aria-label="Loading chat response">
      {/* Summary paragraph lines */}
      <div className="space-y-2">
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-3 w-5/6" />
        <Skeleton className="h-3 w-4/6" />
      </div>
      {/* Stat tiles row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="card py-4 px-5 space-y-2">
            <Skeleton className="h-2.5 w-14" />
            <Skeleton className="h-8 w-20" />
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Sim-result mini-tiles ────────────────────────────────────────────────────

interface SimResultTilesProps {
  result: Record<string, unknown>;
}

function SimResultTiles({ result }: SimResultTilesProps) {
  const et = typeof result.et_quarter_s === "number" ? result.et_quarter_s : null;
  const trap = typeof result.trap_speed_kmh === "number" ? result.trap_speed_kmh : null;
  const et60 = typeof result.et_60ft_s === "number" ? result.et_60ft_s : null;
  const etEighth = typeof result.et_eighth_s === "number" ? result.et_eighth_s : null;
  const bikeName = typeof result.bike_name === "string" ? result.bike_name : null;
  const power = typeof result.peak_power_hp === "number" ? result.peak_power_hp : null;
  const mass = typeof result.total_mass_kg === "number" ? result.total_mass_kg : null;

  return (
    <div className="space-y-3">
      {bikeName && (
        <div className="flex items-center gap-2 text-sm text-carbon-300">
          <Bike className="w-4 h-4 text-signal-500 shrink-0" aria-hidden="true" />
          <span className="font-medium">{bikeName}</span>
          {power != null && (
            <span className="text-carbon-500 text-xs">· {power.toFixed(0)} hp</span>
          )}
          {mass != null && (
            <span className="text-carbon-500 text-xs">· {mass.toFixed(0)} kg total</span>
          )}
        </div>
      )}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <SimTile
          label="Quarter-mile ET"
          value={et != null ? `${et.toFixed(3)} s` : "—"}
          accent
        />
        <SimTile
          label="Trap speed"
          value={trap != null ? `${trap.toFixed(1)} km/h` : "—"}
        />
        <SimTile
          label="60 ft"
          value={et60 != null ? `${et60.toFixed(3)} s` : "—"}
        />
        <SimTile
          label="1/8 mile"
          value={etEighth != null ? `${etEighth.toFixed(3)} s` : "—"}
        />
      </div>
    </div>
  );
}

function SimTile({
  label,
  value,
  accent = false,
}: {
  label: string;
  value: string;
  accent?: boolean;
}) {
  return (
    <div className="card py-3 px-4">
      <div className="text-[10px] uppercase tracking-wider text-carbon-500 mb-1">{label}</div>
      <div
        className={`text-xl font-semibold tabular-nums ${
          accent ? "text-signal-400" : "text-carbon-100"
        }`}
      >
        {value}
      </div>
    </div>
  );
}

// ─── Bike suggestion chips ────────────────────────────────────────────────────

interface SuggestionChipsProps {
  suggestions: ChatBikeSuggestion[];
  onSelect: (s: ChatBikeSuggestion) => void;
}

function SuggestionChips({ suggestions, onSelect }: SuggestionChipsProps) {
  if (suggestions.length === 0) return null;
  return (
    <div className="space-y-2">
      <p className="text-xs text-carbon-400">Did you mean one of these?</p>
      <div className="flex flex-wrap gap-2">
        {suggestions.map((s, i) => (
          <button
            key={s.id ?? i}
            onClick={() => onSelect(s)}
            className="
              inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium
              bg-carbon-800 text-carbon-200 border border-carbon-700
              hover:border-signal-500/60 hover:bg-carbon-700 hover:text-white
              focus-visible:outline-2 focus-visible:outline-signal-500
              transition-colors
            "
          >
            <Zap className="w-3 h-3 text-signal-500" aria-hidden="true" />
            {[s.manufacturer, s.model, s.year_range].filter(Boolean).join(" ")}
          </button>
        ))}
      </div>
    </div>
  );
}

// ─── Error banners ────────────────────────────────────────────────────────────

function LlmNotConfiguredBanner() {
  return (
    <div
      className="flex gap-3 p-4 rounded-lg border border-yellow-500/30 bg-yellow-500/5"
      role="alert"
    >
      <KeyRound className="w-5 h-5 text-yellow-400 shrink-0 mt-0.5" aria-hidden="true" />
      <div>
        <div className="font-medium text-yellow-400 text-sm">LLM not configured</div>
        <div className="text-xs text-carbon-400 mt-1">
          Set the provider API key on the server (default provider is Groq:{' '}
          <code className="font-mono bg-carbon-800 px-1 rounded">GROQ_API_KEY</code>; see{' '}
          <code className="font-mono bg-carbon-800 px-1 rounded">LLM_PROVIDER</code>) to enable
          natural-language queries.
        </div>
      </div>
    </div>
  );
}

function GenericErrorBanner({ detail }: { detail: string | null }) {
  return (
    <div
      className="flex gap-3 p-4 rounded-lg border border-stop-500/30 bg-stop-500/5"
      role="alert"
    >
      <AlertTriangle className="w-5 h-5 text-stop-500 shrink-0 mt-0.5" aria-hidden="true" />
      <div>
        <div className="font-medium text-stop-500 text-sm">Query failed</div>
        {detail && (
          <div className="text-xs text-carbon-400 mt-1">{detail}</div>
        )}
      </div>
    </div>
  );
}

// ─── Result panel ─────────────────────────────────────────────────────────────

interface ResultPanelProps {
  response: ChatResponse;
  onSuggestionClick: (s: ChatBikeSuggestion) => void;
}

function ResultPanel({ response, onSuggestionClick }: ResultPanelProps) {
  const { error, error_detail, bike_suggestions, sim_result, summary, raw_query } = response;

  // llm_not_configured
  if (error === "llm_not_configured") {
    return <LlmNotConfiguredBanner />;
  }

  // bike_not_found — show suggestions
  if (error === "bike_not_found") {
    return (
      <div className="space-y-4">
        <div className="flex gap-3 p-4 rounded-lg border border-carbon-700 bg-carbon-800/40">
          <AlertTriangle className="w-5 h-5 text-yellow-400 shrink-0 mt-0.5" aria-hidden="true" />
          <div className="text-sm text-carbon-300">
            Couldn't find a bike matching{" "}
            <span className="text-carbon-100 italic">"{raw_query}"</span>
            {error_detail ? ` — ${error_detail}` : "."}
          </div>
        </div>
        <SuggestionChips suggestions={bike_suggestions} onSelect={onSuggestionClick} />
      </div>
    );
  }

  // parse_failed or sim_failed
  if (error === "parse_failed" || error === "sim_failed") {
    return <GenericErrorBanner detail={error_detail} />;
  }

  // Other unexpected error string
  if (error) {
    return <GenericErrorBanner detail={error_detail ?? error} />;
  }

  // Success path
  return (
    <div className="space-y-4">
      {sim_result && <SimResultTiles result={sim_result} />}
      {summary && (
        <div className="text-sm text-carbon-300 leading-relaxed border-l-2 border-signal-500/40 pl-3">
          {summary}
        </div>
      )}
    </div>
  );
}

// ─── Example prompts ──────────────────────────────────────────────────────────

const EXAMPLE_QUERIES = [
  "How fast is a Kawasaki Ninja 400 at Aamby Valley?",
  "How does my K5 run in 40°C heat?",
  "What quarter-mile time can I expect from an R15 V4?",
  "Compare Hayabusa vs ZX-14R at sea level",
];

// ─── Main ChatBox ──────────────────────────────────────────────────────────────

export interface ChatBoxProps {
  /**
   * Called when the user clicks a bike suggestion chip.
   * The parent should use this to switch to the Simulate tab
   * and pre-select the suggested bike.
   */
  onSuggestionClick: (suggestion: ChatBikeSuggestion) => void;
}

export function ChatBox({ onSuggestionClick }: ChatBoxProps) {
  const [query, setQuery] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const chat = useChat();

  const canSubmit = query.trim().length > 0 && !chat.isPending;

  const submit = useCallback(() => {
    const q = query.trim();
    if (!q) return;
    chat.mutate({ query: q, run_summary: true });
  }, [query, chat]);

  // Enter submits; Shift+Enter inserts a newline (standard chat UX).
  // isComposing guards against IME composition (e.g. Japanese / Chinese input)
  // where the Enter keystroke is part of selecting a candidate, not a submit.
  const onKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
        e.preventDefault();
        submit();
      }
    },
    [submit],
  );

  // Auto-resize textarea up to ~6 lines
  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = `${Math.min(ta.scrollHeight, 150)}px`;
  }, [query]);

  const fillExample = (ex: string) => {
    setQuery(ex);
    textareaRef.current?.focus();
  };

  return (
    <div className="space-y-5">
      {/* Input + submit */}
      <div className="card p-4 space-y-3">
        <label className="block text-xs uppercase tracking-wider text-carbon-500">
          Ask MotoQuant
        </label>

        <div className="flex gap-2 items-end">
          <textarea
            ref={textareaRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="e.g. How fast is a Ninja 400 in 35°C heat at Aamby Valley?"
            rows={2}
            className="
              input flex-1 resize-none min-h-[2.5rem] leading-snug
              focus-visible:outline-2 focus-visible:outline-signal-500
            "
            aria-label="Natural-language query"
            aria-multiline="true"
            disabled={chat.isPending}
          />
          <button
            onClick={submit}
            disabled={!canSubmit}
            className="btn btn-primary self-end shrink-0 focus-visible:outline-2 focus-visible:outline-signal-300"
            aria-label="Send query"
            title="Send (Enter)"
          >
            {chat.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
            ) : (
              <Send className="w-4 h-4" aria-hidden="true" />
            )}
          </button>
        </div>

        <p className="text-[10px] text-carbon-600">
          Press <kbd className="font-mono bg-carbon-800 px-1 rounded">Enter</kbd> to submit · <kbd className="font-mono bg-carbon-800 px-1 rounded">Shift+Enter</kbd> for newline
        </p>

        {/* Example prompts — only shown before first query */}
        {!chat.data && !chat.isPending && (
          <div className="space-y-1.5">
            <p className="text-[10px] uppercase tracking-wider text-carbon-600">
              Try an example
            </p>
            <div className="flex flex-wrap gap-1.5">
              {EXAMPLE_QUERIES.map((ex) => (
                <button
                  key={ex}
                  onClick={() => fillExample(ex)}
                  className="
                    text-[11px] px-2.5 py-1 rounded-full
                    bg-carbon-800 text-carbon-400 border border-carbon-700
                    hover:text-carbon-200 hover:border-carbon-600
                    focus-visible:outline-2 focus-visible:outline-signal-500
                    transition-colors
                  "
                >
                  {ex}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Network-level error (shouldn't happen often — recoverable app errors
          come back as HTTP 200 with response.error set) */}
      {chat.isError && (
        <div
          className="card p-4 border-stop-500/40 bg-stop-500/5 flex gap-3"
          role="alert"
        >
          <AlertTriangle className="w-5 h-5 text-stop-500 shrink-0 mt-0.5" aria-hidden="true" />
          <div>
            <div className="font-medium text-stop-500 text-sm">Request failed</div>
            <div className="text-xs text-carbon-400 mt-1">
              {chat.error?.message ?? "Check that the backend is running."}
            </div>
          </div>
        </div>
      )}

      {/* Loading skeleton */}
      {chat.isPending && (
        <div className="card p-5">
          <ChatSkeleton />
        </div>
      )}

      {/* Result */}
      {chat.data && !chat.isPending && (
        <div className="card p-5">
          <ResultPanel response={chat.data} onSuggestionClick={onSuggestionClick} />
        </div>
      )}
    </div>
  );
}
