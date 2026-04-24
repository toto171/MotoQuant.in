// Keyboard shortcuts reference modal — triggered by pressing `?`.
// Shows all navigation + page-level shortcuts.

import { X, Keyboard } from "lucide-react";
import { useEffect } from "react";

const GROUPS = [
  {
    label: "Navigation",
    shortcuts: [
      { keys: ["g", "s"], label: "Go to Simulate" },
      { keys: ["g", "b"], label: "Go to Bikes" },
      { keys: ["g", "u"], label: "Go to Build" },
      { keys: ["g", "c"], label: "Go to Compare" },
      { keys: ["g", "h"], label: "Go to History" },
    ],
  },
  {
    label: "Simulate page",
    shortcuts: [
      { keys: ["r"], label: "Re-run simulation" },
      { keys: ["s"], label: "Save current run" },
      { keys: ["e"], label: "Export PDF report" },
    ],
  },
  {
    label: "Global",
    shortcuts: [
      { keys: ["/"], label: "Focus search / bike picker" },
      { keys: ["?"], label: "Open this shortcuts guide" },
      { keys: ["Esc"], label: "Close modal / clear search" },
    ],
  },
] as const;

interface Props {
  onClose: () => void;
}

export function KeyboardShortcutsModal({ onClose }: Props) {
  // Close on Escape.
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-carbon-950/80 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      role="dialog"
      aria-modal="true"
      aria-label="Keyboard shortcuts"
    >
      <div className="card w-full max-w-lg p-6 shadow-2xl">
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2">
            <Keyboard className="w-4 h-4 text-signal-500" aria-hidden="true" />
            <h2 className="font-semibold text-carbon-100">Keyboard shortcuts</h2>
          </div>
          <button
            onClick={onClose}
            className="text-carbon-500 hover:text-carbon-100 transition-colors"
            aria-label="Close shortcuts modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="space-y-5">
          {GROUPS.map((group) => (
            <div key={group.label}>
              <div className="text-[10px] uppercase tracking-wider text-carbon-500 mb-2">
                {group.label}
              </div>
              <div className="space-y-1.5">
                {group.shortcuts.map((s) => (
                  <div
                    key={s.keys.join("+")}
                    className="flex items-center justify-between text-sm"
                  >
                    <span className="text-carbon-300">{s.label}</span>
                    <div className="flex items-center gap-1">
                      {s.keys.map((k, i) => (
                        <span key={k} className="flex items-center gap-1">
                          {i > 0 && (
                            <span className="text-carbon-600 text-xs">then</span>
                          )}
                          <kbd className="inline-flex items-center justify-center rounded bg-carbon-700 border border-carbon-600 px-1.5 py-0.5 font-mono text-xs text-carbon-200 min-w-[1.6rem]">
                            {k}
                          </kbd>
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-5 pt-4 border-t border-carbon-800 text-xs text-carbon-600">
          Shortcuts are disabled when typing in an input field.
        </div>
      </div>
    </div>
  );
}
