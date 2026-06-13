import { NavLink } from "react-router-dom";
import {
  Gauge,
  SlidersHorizontal,
  Bike,
  Wrench,
  GitCompare,
  History,
  Settings,
  Zap,
} from "lucide-react";
import clsx from "clsx";

const NAV = [
  { to: "/simulate", label: "Simulate", Icon: Gauge },
  { to: "/bikes", label: "Bikes", Icon: Bike },
  { to: "/build", label: "Build", Icon: Wrench },
  { to: "/autotune", label: "Autotune", Icon: SlidersHorizontal },
  { to: "/compare", label: "Compare", Icon: GitCompare },
  { to: "/history", label: "History", Icon: History },
  { to: "/settings", label: "Settings", Icon: Settings },
];

export function Sidebar() {
  return (
    <aside className="w-60 shrink-0 bg-carbon-900 border-r border-white/10 flex flex-col">
      <div className="h-14 flex items-center gap-2.5 px-5 border-b border-white/10">
        <div className="w-8 h-8 rounded bg-signal-500 flex items-center justify-center shadow-glow">
          <Zap className="w-4 h-4 text-carbon-950" strokeWidth={3} />
        </div>
        <div>
          <div className="font-semibold text-sm leading-tight tracking-tight">MotoQuant</div>
          <div className="label text-[10px] text-signal-500/80">Pro</div>
        </div>
      </div>

      <nav className="flex-1 p-3 space-y-0.5">
        {NAV.map(({ to, label, Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              clsx(
                "flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors border-l-2",
                isActive
                  ? "bg-carbon-800 text-white border-signal-500"
                  : "text-carbon-400 border-transparent hover:text-carbon-100 hover:bg-carbon-800/60",
              )
            }
          >
            <Icon className="w-4 h-4" />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="p-3 border-t border-white/10 leading-relaxed">
        <div className="label text-[10px] text-carbon-500">The physics of faster.</div>
        <div className="mt-1 text-[10px] text-carbon-600 font-mono">
          v0.5.0 · Tauri preview
        </div>
      </div>
    </aside>
  );
}
