import { ReactNode } from "react";
import clsx from "clsx";

interface Props {
  label: string;
  value: ReactNode;
  unit?: string;
  hint?: ReactNode;
  accent?: "signal" | "go" | "warn" | "stop" | "plain";
}

const accentColor = {
  signal: "text-signal-500",
  go: "text-go-500",
  warn: "text-warn-500",
  stop: "text-stop-500",
  plain: "text-carbon-100",
} as const;

export function StatTile({
  label,
  value,
  unit,
  hint,
  accent = "plain",
}: Props) {
  return (
    <div className="card py-4 px-5">
      <div className="text-[10px] uppercase tracking-wider text-carbon-500 mb-1">
        {label}
      </div>
      <div className={clsx("stat-number", accentColor[accent])}>
        {value}
        {unit && (
          <span className="ml-1 text-sm font-normal text-carbon-400">
            {unit}
          </span>
        )}
      </div>
      {hint && (
        <div className="mt-1 text-[11px] text-carbon-500">{hint}</div>
      )}
    </div>
  );
}
