// Shared engine status hook.
// Polls /api/health every 15 s (same interval as TopBar).
// React Query serves the cached result so no extra HTTP calls are made;
// all hooks sharing queryKey: ["health"] receive the same promise.

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useEngineStatus() {
  const q = useQuery({
    queryKey: ["health"],
    queryFn: () => api.health(),
    refetchInterval: 15_000,
    retry: 0,
  });

  return {
    online: q.isSuccess,
    offline: q.isError,
    loading: q.isPending,
  };
}
