import { useCallback, useRef, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, runJob } from "@/lib/api";
import type {
  CompareRequest,
  CompareResponse,
  QuickSimRequest,
  QuickSimResponse,
  SaveRunRequest,
  SaveRunResponse,
  SimulateRequest,
  SimulateResponse,
  SurrogateCompareRequest,
  SurrogateCompareResponse,
  SurrogatePredictRequest,
  SurrogatePredictResponse,
  OptimizeBuildRequest,
  OptimizedBuild,
  AutotuneRequest,
  EcuAutotune,
  JobKind,
  JobProgress,
} from "@/types/api";

export function useBikes(params: {
  search?: string;
  manufacturer?: string;
  category?: string;
  limit?: number;
  offset?: number;
} = {}) {
  return useQuery({
    queryKey: ["bikes", params],
    queryFn: () => api.listBikes(params),
    placeholderData: (prev) => prev,
  });
}

export function useBike(id: number | null) {
  return useQuery({
    queryKey: ["bike", id],
    queryFn: () => api.getBike(id!),
    enabled: id != null,
  });
}

export function useVenues() {
  return useQuery({
    queryKey: ["venues"],
    queryFn: () => api.listVenues(),
  });
}

export function usePartsCategories() {
  return useQuery({
    queryKey: ["parts-categories"],
    queryFn: () => api.listPartsCategories(),
  });
}

export function useParts(params: {
  category?: string;
  bike_id?: number;
  compatible_only?: boolean;
  search?: string;
  limit?: number;
} = {}) {
  return useQuery({
    queryKey: ["parts", params],
    queryFn: () => api.listParts(params),
    placeholderData: (prev) => prev,
  });
}

export function useSimulate() {
  return useMutation<SimulateResponse, Error, SimulateRequest>({
    mutationFn: (req) => api.simulate(req),
  });
}

export function useQuickSimulate() {
  return useMutation<QuickSimResponse, Error, QuickSimRequest>({
    mutationFn: (req) => api.simulateQuick(req),
  });
}

export function useCompare() {
  return useMutation<CompareResponse, Error, CompareRequest>({
    mutationFn: (req) => api.simulateCompare(req),
  });
}

export function useLeaderboard(limit = 20, enabled = true) {
  return useQuery({
    queryKey: ["leaderboard", limit],
    queryFn: () => api.leaderboard({ limit }),
    staleTime: 30_000, // sim_runs doesn't update often; 30s is fine
    enabled,
  });
}

// Personal saved-run history for the signed-in user (History tab). Distinct
// from useLeaderboard, which is the global top-runs board.
export function useMyRuns(limit = 25, enabled = true) {
  return useQuery({
    queryKey: ["my-runs", limit],
    queryFn: () => api.myRuns({ limit }),
    staleTime: 30_000,
    enabled,
  });
}

export function useSaveRun() {
  const qc = useQueryClient();
  return useMutation<SaveRunResponse, Error, SaveRunRequest>({
    mutationFn: (req) => api.saveRun(req),
    onSuccess: () => {
      // Refresh the leaderboard so the newly-saved run shows up immediately
      // on the History tab without waiting for staleTime to expire.
      qc.invalidateQueries({ queryKey: ["leaderboard"] });
    },
  });
}

// ─── Surrogate-model preview hooks ────────────────────────────────────
// Use these in BuildPage to deliver near-instant feedback on slider /
// part-toggle changes. The full physics sim takes ~50 ms over HTTP; the
// surrogate is ~1-3 ms inference.  Always cross-check against
// useQuickSimulate() before saving a run, since out-of-distribution
// builds may trigger envelope_violations and lower confidence.

export function useSurrogatePredict() {
  return useMutation<SurrogatePredictResponse, Error, SurrogatePredictRequest>({
    mutationFn: (req) => api.surrogatePredict(req),
  });
}

export function useSurrogateCompare() {
  return useMutation<SurrogateCompareResponse, Error, SurrogateCompareRequest>({
    mutationFn: (req) => api.surrogateCompare(req),
  });
}

// ─── Build optimizer + ECU autotune (Track B) ─────────────────────────
export function useOptimizeBuild() {
  return useMutation<OptimizedBuild, Error, OptimizeBuildRequest>({
    mutationFn: (req) => api.optimizeBuild(req),
  });
}

export function useAutotuneEcu() {
  return useMutation<EcuAutotune, Error, AutotuneRequest>({
    mutationFn: (req) => api.autotuneEcu(req),
  });
}

// ─── Background-job runner hook ──────────────────────────────────────────
// Long-running work (full sim, optimise, autotune) runs server-side with real
// progress; this hook drives runJob() and exposes { run, stop, isRunning,
// progress, stage, data, error, reset }. Quick-sim stays synchronous (use
// useQuickSimulate) — polling would only make a ~50 ms call feel slower.
//
// `stop()` aborts the in-flight request AND cancels the job server-side, so a
// user can change the setup mid-run without leaving a zombie burning CPU.
// AbortError is swallowed (a deliberate Stop is not an error tile).

interface JobRunState<T> {
  run: (body: unknown) => Promise<T | undefined>;
  stop: () => void;
  reset: () => void;
  isRunning: boolean;
  progress: number | null;
  stage: string;
  status: JobProgress["status"] | "idle";
  data: T | null;
  error: Error | null;
}

function useJobRunner<T>(
  kind: JobKind,
  fallback?: (body: unknown) => Promise<T>,
): JobRunState<T> {
  const [isRunning, setRunning] = useState(false);
  const [progress, setProgress] = useState<number | null>(null);
  const [stage, setStage] = useState("");
  const [status, setStatus] = useState<JobProgress["status"] | "idle">("idle");
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    setRunning(false);
    setProgress(null);
    setStage("");
    setStatus("idle");
    setData(null);
    setError(null);
  }, []);

  const stop = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  const run = useCallback(
    async (body: unknown): Promise<T | undefined> => {
      // Abort any prior run before starting a new one.
      abortRef.current?.abort();
      const ac = new AbortController();
      abortRef.current = ac;
      setRunning(true);
      setData(null);
      setError(null);
      setProgress(null);
      setStatus("connecting");
      setStage("");
      try {
        const result = await runJob<T>(kind, body, {
          signal: ac.signal,
          fallback: fallback ? () => fallback(body) : undefined,
          onProgress: (p) => {
            setStatus(p.status);
            setProgress(p.progress);
            setStage(p.stage);
          },
        });
        setData(result);
        setRunning(false);
        setStatus("done");
        return result;
      } catch (err) {
        // A deliberate Stop unwinds as AbortError — clear state, no error tile.
        if (err instanceof DOMException && err.name === "AbortError") {
          setRunning(false);
          setStatus("idle");
          setProgress(null);
          setStage("");
          return undefined;
        }
        setError(err instanceof Error ? err : new Error(String(err)));
        setRunning(false);
        setStatus("error");
        return undefined;
      }
    },
    [kind, fallback],
  );

  return { run, stop, reset, isRunning, progress, stage, status, data, error };
}

// Full quarter-mile simulation as a background job (real progress + Stop).
// Falls back to the synchronous /api/simulate when /api/jobs/* is absent.
export function useSimulateJob() {
  const fallback = useCallback(
    (body: unknown) => api.simulate(body as SimulateRequest),
    [],
  );
  return useJobRunner<SimulateResponse>("simulate", fallback);
}

// Build optimiser as a background job (it can run for minutes when the
// surrogate is unavailable and every candidate is a full RK4 sim).
export function useOptimizeBuildJob() {
  const fallback = useCallback(
    (body: unknown) => api.optimizeBuild(body as OptimizeBuildRequest),
    [],
  );
  return useJobRunner<OptimizedBuild>("optimize", fallback);
}

// ECU autotune as a background job (sweeps gearing + launch RPM on the full
// sim — slow on a constrained instance).
export function useAutotuneJob() {
  const fallback = useCallback(
    (body: unknown) => api.autotuneEcu(body as AutotuneRequest),
    [],
  );
  return useJobRunner<EcuAutotune>("autotune", fallback);
}

