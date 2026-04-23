import { NavLink } from "react-router-dom";
import {
  Gauge,
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
  { to: "/compare", label: "Compare", Icon: GitCompare },
  { to: "/history", label: "History", Icon: History },
  { to: "/settings", label: "Settings", Icon: Settings },
];

export function Sidebar() {
  return (
    <aside className="w-60 shrink-0 bg-carbon-900 border-r border-carbon-800 flex flex-col">
      <div className="h-14 flex items-center gap-2 px-5 border-b border-carbon-800">
        <div className="w-8 h-8 rounded bg-signal-600 flex items-center justify-center">
          <Zap className="w-4 h-4 text-carbon-950" strokeWidth={3} />
        </div>
        <div>
          <div className="font-semibold text-sm leading-tight">MotoQuant</div>
          <div className="text-[10px] uppercase tracking-wide text-carbon-500">
            Pro
          </div>
        </div>
      </div>

      <nav className="flex-1 p-3 space-y-0.5">
        {NAV.map(({ to, label, Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              clsx(
                "flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors",
                isActive
                  ? "bg-carbon-800 text-white"
                  : "text-carbon-400 hover:text-carbon-100 hover:bg-carbon-800/60",
              )
            }
          >
            <Icon className="w-4 h-4" />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="p-3 border-t border-carbon-800 text-[10px] text-carbon-500 leading-relaxed">
        <div>The physics of faster.</div>
        <div className="mt-1 text-carbon-600">
          v0.5.0 · Tauri preview
        </div>
      </div>
    </aside>
  );
}
