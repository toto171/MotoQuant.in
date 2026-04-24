// Toast notification stack — renders in a fixed bottom-right portal.
// Max 3 visible at once; each auto-dismisses after 3 s (set in toastStore).

import { X, CheckCircle2, AlertCircle, AlertTriangle, Info } from "lucide-react";
import clsx from "clsx";
import { useToastStore } from "@/store/toastStore";
import type { ToastVariant } from "@/store/toastStore";

const META: Record<
  ToastVariant,
  { Icon: React.ComponentType<{ className?: string }>; classes: string }
> = {
  success: {
    Icon: CheckCircle2,
    classes: "border-go-500/40 bg-go-500/10 text-go-500",
  },
  error: {
    Icon: AlertCircle,
    classes: "border-stop-500/40 bg-stop-500/10 text-stop-500",
  },
  warn: {
    Icon: AlertTriangle,
    classes: "border-warn-500/40 bg-warn-500/10 text-warn-500",
  },
  info: {
    Icon: Info,
    classes: "border-signal-500/40 bg-signal-500/10 text-signal-400",
  },
};

export function ToastStack() {
  const { toasts, dismiss } = useToastStore();

  if (toasts.length === 0) return null;

  return (
    <div
      className="fixed bottom-6 right-6 z-50 flex flex-col gap-2 pointer-events-none"
      role="region"
      aria-label="Notifications"
    >
      {toasts.map((t) => {
        const { Icon, classes } = META[t.variant];
        return (
          <div
            key={t.id}
            className={clsx(
              "pointer-events-auto flex items-center gap-3 rounded-lg border px-4 py-3 shadow-xl text-sm",
              "animate-in slide-in-from-bottom-2 fade-in duration-200",
              classes,
            )}
            role="alert"
          >
            <Icon className="w-4 h-4 shrink-0" aria-hidden="true" />
            <span className="flex-1 text-carbon-100">{t.message}</span>
            <button
              onClick={() => dismiss(t.id)}
              className="text-carbon-500 hover:text-carbon-200 ml-1 shrink-0"
              aria-label="Dismiss notification"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        );
      })}
    </div>
  );
}
