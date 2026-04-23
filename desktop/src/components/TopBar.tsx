import { useQuery } from "@tanstack/react-query";
import { api, getResolvedBaseUrl } from "@/lib/api";

export function TopBar() {
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
    <header className="h-14 shrink-0 border-b border-carbon-800 bg-carbon-900/60 backdrop-blur flex items-center justify-between px-6">
      <div className="text-xs uppercase tracking-widest text-carbon-500">
        First-principles motorcycle drag simulation
      </div>
      <div className="flex items-center gap-3 text-xs">
        <span
          className={
            online
              ? "chip chip-success"
              : failed
                ? "chip chip-danger"
                : "chip"
          }
        >
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              online
                ? "bg-go-500"
                : failed
                  ? "bg-stop-500"
                  : "bg-warn-500 animate-pulse"
            }`}
          />
          {online ? "Engine online" : failed ? "Engine offline" : "Starting..."}
        </span>
        {baseUrl.data && (
          <span className="text-[10px] text-carbon-600 font-mono">
            {baseUrl.data.replace(/^https?:\/\//, "")}
          </span>
        )}
      </div>
    </header>
  );
}
