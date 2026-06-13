import { useQuery } from "@tanstack/react-query";
import { Menu, LogOut } from "lucide-react";
import { api, getResolvedBaseUrl } from "@/lib/api";
import { useSidebar } from "@/components/Layout";
import { useAuth } from "@/contexts/AuthContext";

export function TopBar() {
  const { toggle } = useSidebar();
  const { user, tier, logout } = useAuth();

  const health = useQuery({
    queryKey: ["health"],
    queryFn: () => api.health(),
    refetchInterval: 15_000,
    retry: 0,
  });

  const baseUrl = useQuery({
    queryKey: ["backend-url"],
    queryFn: () => getResolvedBaseUrl(),
    staleTime: Infinity,
  });

  const online = health.isSuccess;
  const failed = health.isError;

  return (
    <header className="h-14 shrink-0 border-b border-white/10 bg-carbon-900/60 backdrop-blur flex items-center justify-between px-4 md:px-6">
      <div className="flex items-center gap-3">
        <button
          onClick={toggle}
          className="text-carbon-400 hover:text-carbon-100 transition-colors p-1 rounded focus-visible:outline-2 focus-visible:outline-signal-500"
          aria-label="Toggle navigation sidebar"
          title="Toggle sidebar"
        >
          <Menu className="w-5 h-5" aria-hidden="true" />
        </button>
        <div className="hidden sm:block label text-[10px] text-carbon-500">
          Hosted motorcycle drag simulation
        </div>
      </div>

      <div className="flex items-center gap-3 text-xs">
        <span
          className={
            online ? "chip chip-success" : failed ? "chip chip-danger" : "chip"
          }
          aria-label={online ? "Connected to MotoQuant servers" : failed ? "MotoQuant servers unreachable" : "Connecting to MotoQuant servers"}
        >
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              online ? "bg-go-500" : failed ? "bg-stop-500" : "bg-warn-500 animate-pulse"
            }`}
            aria-hidden="true"
          />
          {online ? "Connected" : failed ? "Offline" : "Connecting…"}
        </span>
        {baseUrl.data && (
          <span className="hidden md:block text-[10px] text-carbon-600 font-mono">
            {baseUrl.data.replace(/^https?:\/\//, "")}
          </span>
        )}
        <span
          className="hidden sm:block text-[10px] text-carbon-700 select-none"
          title="Press ? for keyboard shortcuts"
        >
          ? shortcuts
        </span>
        {user && (
          <div className="flex items-center gap-2">
            <span
              className="hidden md:inline text-[10px] text-carbon-500 max-w-[14rem] truncate"
              title={`${user.email}${tier ? ` · ${tier}` : ""}`}
            >
              {user.email}
              {tier ? ` · ${tier}` : ""}
            </span>
            <button
              onClick={() => void logout()}
              className="text-carbon-400 hover:text-carbon-100 transition-colors p-1 rounded focus-visible:outline-2 focus-visible:outline-signal-500"
              aria-label="Sign out"
              title="Sign out"
            >
              <LogOut className="w-4 h-4" aria-hidden="true" />
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
