// Typed fetch client for the MotoQuant FastAPI backend.
//
// In production the backend is a Python sidecar spawned by Tauri on an
// ephemeral port. The `tauri::command get_backend_url` on the Rust side
// reports the actual URL; we cache it once on first call. During `vite dev`
// (browser-only, no Tauri shell) we fall back to VITE_API_URL or the common
// `uvicorn motoquant.api:app --port 8000` default.

import type {
  ApiError,
  BikeDetail,
  BikesListResponse,
  ChatRequest,
  ChatResponse,
  CompareRequest,
  CompareResponse,
  LeaderboardResponse,
  PartsCategoriesResponse,
  PartsResponse,
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
  TiresResponse,
  VenuesResponse,
  OptimizeBuildRequest,
  OptimizedBuild,
  AutotuneRequest,
  EcuAutotune,
  JobKind,
  JobStartResponse,
  JobStatusResponse,
  JobProgress,
} from "@/types/api";

// ─── Base-URL resolution ─────────────────────────────────────────────────

let cachedBaseUrl: string | null = null;
let baseUrlPromise: Promise<string> | null = null;

const VITE_API_URL = import.meta.env.VITE_API_URL as string | undefined;
const DEV_FALLBACK = "http://127.0.0.1:8000";

function isTauriRuntime(): boolean {
  return typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;
}

async function resolveBaseUrl(): Promise<string> {
  if (cachedBaseUrl) return cachedBaseUrl;
  if (baseUrlPromise) return baseUrlPromise;

  baseUrlPromise = (async () => {
    if (isTauriRuntime()) {
      try {
        const { invoke } = await import("@tauri-apps/api/core");
        const url = await invoke<string>("get_backend_url");
        cachedBaseUrl = url.replace(/\/$/, "");
        return cachedBaseUrl;
      } catch (err) {
        // Fall through to env / dev fallback if the Rust command isn't ready.
        console.warn("[api] Tauri get_backend_url failed, falling back:", err);
      }
    }
    const fromEnv = VITE_API_URL && VITE_API_URL.replace(/\/$/, "");
    cachedBaseUrl = fromEnv || DEV_FALLBACK;
    return cachedBaseUrl;
  })();

  return baseUrlPromise;
}

// ─── Fetch helpers ───────────────────────────────────────────────────────

class ApiRequestError extends Error implements ApiError {
  status: number;
  detail: string;
  constructor(status: number, detail: string) {
    super(`${status}: ${detail}`);
    this.status = status;
    this.detail = detail;
  }
}

async function request<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const base = await resolveBaseUrl();
  const headers: HeadersInit = {
    Accept: "application/json",
    ...(init.body && !(init.body instanceof FormData)
      ? { "Content-Type": "application/json" }
      : {}),
    ...(init.headers || {}),
  };

  let response: Response;
  try {
    response = await fetch(`${base}${path}`, { ...init, headers });
  } catch (err) {
    throw new ApiRequestError(
      0,
      err instanceof Error ? err.message : "Network unreachable",
    );
  }

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      if (typeof body?.detail === "string") detail = body.detail;
      else if (body?.detail) detail = JSON.stringify(body.detail);
    } catch {
      // Non-JSON body — keep statusText.
    }
    throw new ApiRequestError(response.status, detail);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

const qs = (params: Record<string, unknown>): string => {
  const parts: string[] = [];
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null || v === "") continue;
    parts.push(`${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`);
  }
  return parts.length ? `?${parts.join("&")}` : "";
};

// ─── Endpoints ───────────────────────────────────────────────────────────

export const api = {
  health: () => request<{ status: string; version?: string }>("/api/health"),

  // Bikes
  listBikes: (params: {
    search?: string;
    manufacturer?: string;
    category?: string;
    limit?: number;
    offset?: number;
  } = {}) => request<BikesListResponse>(`/api/bikes${qs(params)}`),

  getBike: (id: number) => request<BikeDetail>(`/api/bikes/${id}`),

  // Venues
  listVenues: () => request<VenuesResponse>("/api/venues"),

  // Tires
  listTires: (params: {
    compound?: string;
    manufacturer?: string;
    limit?: number;
  } = {}) => request<TiresResponse>(`/api/tires${qs(params)}`),

  // Parts
  listPartsCategories: () =>
    request<PartsCategoriesResponse>("/api/parts/categories"),

  listParts: (params: {
    category?: string;
    category_id?: number;
    bike_id?: number;
    compatible_only?: boolean;
    search?: string;
    limit?: number;
  } = {}) => request<PartsResponse>(`/api/parts${qs(params)}`),

  // Simulation
  simulate: (req: SimulateRequest) =>
    request<SimulateResponse>("/api/simulate", {
      method: "POST",
      body: JSON.stringify(req),
    }),

  simulateQuick: (req: QuickSimRequest) =>
    request<QuickSimResponse>("/api/simulate/quick", {
      method: "POST",
      body: JSON.stringify(req),
    }),

  simulateCompare: (req: CompareRequest) =>
    request<CompareResponse>("/api/simulate/compare", {
      method: "POST",
      body: JSON.stringify(req),
    }),

  // Persist a single simulation result to sim_runs (shows up on the
  // leaderboard + History tab). bike_id is bike_models.id; the server
  // resolves it to bike_configs.id internally.
  saveRun: (req: SaveRunRequest) =>
    request<SaveRunResponse>("/api/simulate/save", {
      method: "POST",
      body: JSON.stringify(req),
    }),

  // Leaderboard (top saved runs from local sim_runs table)
  leaderboard: (params: { limit?: number } = {}) =>
    request<LeaderboardResponse>(`/api/leaderboard${qs(params)}`),

  // Natural-language chat (Phase A — POST /api/chat)
  chat: (req: ChatRequest) =>
    request<ChatResponse>("/api/chat", {
      method: "POST",
      body: JSON.stringify(req),
    }),

  // ─── Surrogate model inference ───────────────────────────────────────
  // Fast (target p95 < 5 ms) ET/trap prediction via the trained DNN/XGB
  // surrogate. Used by BuildPage for slider-tick previews; falls back to
  // simulateQuick when within_training_envelope is false.
  surrogatePredict: (req: SurrogatePredictRequest) =>
    request<SurrogatePredictResponse>("/api/surrogate/predict", {
      method: "POST",
      body: JSON.stringify(req),
    }),

  surrogateCompare: (req: SurrogateCompareRequest) =>
    request<SurrogateCompareResponse>("/api/surrogate/compare", {
      method: "POST",
      body: JSON.stringify(req),
    }),

  // ─── Build optimizer + ECU autotune (Track B) ───────────────────────
  optimizeBuild: (req: OptimizeBuildRequest) =>
    request<OptimizedBuild>("/api/optimize/build", {
      method: "POST",
      body: JSON.stringify(req),
    }),

  autotuneEcu: (req: AutotuneRequest) =>
    request<EcuAutotune>("/api/autotune/ecu", {
      method: "POST",
      body: JSON.stringify(req),
    }),

  // ─── Background jobs (real progress) ─────────────────────────────────
  // POST /api/jobs/{kind} → 202 { job_id }; GET /api/jobs/{id} polls
  // { status, progress, stage, result|error }; POST /api/jobs/{id}/cancel
  // stops it. Use runJob() rather than these directly — it polls, backs
  // off, tolerates transient blips, and falls back to the sync route.
  startJob: (kind: JobKind, body: unknown, signal?: AbortSignal) =>
    request<JobStartResponse>(`/api/jobs/${kind}`, {
      method: "POST",
      body: JSON.stringify(body),
      signal,
    }),

  getJobRaw: (jobId: string, signal?: AbortSignal) =>
    request<JobStatusResponse>(`/api/jobs/${jobId}`, { signal }),

  cancelJob: (jobId: string) =>
    request<unknown>(`/api/jobs/${jobId}/cancel`, { method: "POST" }),
};

export { ApiRequestError };

// ─── runJob: failure-tolerant job poller ─────────────────────────────────
// Mirrors the web lib/api.js behaviour so desktop + web share one contract:
//   • transient errors (network / 5xx / proxy) tolerated up to 60 s
//   • 404 must repeat 3× in a row before the registry is declared lost (a
//     real backend restart) — then re-submit the pure-compute job ONCE
//   • poll interval backs off 350 ms → 800 ms → 1.5 s as the job ages
//   • AbortSignal cancels the job server-side and unwinds like a fetch abort
//   • on 404/405 at submit time (backend predates /api/jobs/*, e.g. an older
//     bundled sidecar) we transparently fall back to the synchronous route
//
// `fallback` runs the equivalent sync request; it MUST resolve to the same
// result shape the job would have produced.

export interface RunJobOptions<T> {
  onProgress?: (p: JobProgress) => void;
  fallback?: () => Promise<T>;
  pollMs?: number;
  signal?: AbortSignal;
}

function isMissingJobsRoute(err: unknown): boolean {
  if (err instanceof ApiRequestError) return err.status === 404 || err.status === 405;
  return false;
}

const sleep = (ms: number) =>
  new Promise<void>((resolve) => setTimeout(resolve, ms));

export async function runJob<T>(
  kind: JobKind,
  body: unknown,
  { onProgress, fallback, pollMs = 350, signal }: RunJobOptions<T> = {},
): Promise<T> {
  onProgress?.({ status: "connecting", progress: null, stage: "" });

  let started: JobStartResponse;
  try {
    started = await api.startJob(kind, body, signal);
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") throw err;
    if (fallback && isMissingJobsRoute(err)) {
      onProgress?.({ status: "running", progress: null, stage: "" });
      return fallback();
    }
    throw err;
  }

  const abort = (): DOMException => {
    // Stop button: free the server slot, then unwind like a fetch abort.
    api.cancelJob(started.job_id).catch(() => {});
    return new DOMException("Aborted", "AbortError");
  };
  if (signal?.aborted) throw abort();

  let t0 = Date.now();
  let lastSuccessAt = Date.now();
  let lostCount = 0;
  let restarts = 0;

  for (;;) {
    let j: JobStatusResponse | null = null;
    let lost = false;
    try {
      j = await api.getJobRaw(started.job_id, signal);
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") throw abort();
      if (err instanceof ApiRequestError && err.status === 404) {
        lost = true; // registry may have dropped it — confirm 3× below
      }
      // other transient errors (network / 5xx) tolerated by the timeout gate
    }

    if (j != null) {
      lastSuccessAt = Date.now();
      lostCount = 0;
      if (signal?.aborted) throw abort();
      if (j.status === "cancelled") throw new DOMException("Aborted", "AbortError");
      if (j.status === "error") throw new Error(j.error || "Simulation failed");
      onProgress?.({ status: j.status, progress: j.progress, stage: j.stage });
      if (j.status === "done") return j.result as T;
    } else if (lost) {
      lostCount += 1;
      if (lostCount >= 3) {
        // In-memory registry: a backend restart (deploy / crash) loses the
        // job. Sims are pure compute, so re-submit the same work once.
        if (restarts >= 1) {
          throw new Error(
            "Progress lost (the engine restarted mid-run) — please run again",
          );
        }
        restarts += 1;
        lostCount = 0;
        onProgress?.({
          status: "connecting",
          progress: null,
          stage: "Engine restarted — running again from the start",
        });
        try {
          started = await api.startJob(kind, body, signal);
        } catch (err) {
          if (err instanceof DOMException && err.name === "AbortError") throw abort();
          throw new Error(
            "Progress lost and the engine is not reachable — please run again",
          );
        }
        lastSuccessAt = Date.now();
        t0 = Date.now(); // restart the backoff for the new job
        continue;
      }
    } else if (Date.now() - lastSuccessAt > 60_000) {
      api.cancelJob(started.job_id).catch(() => {}); // don't leave a zombie burning CPU
      throw new Error(
        "Connection lost while the simulation was running — check your network and run again",
      );
    }

    const age = Date.now() - t0;
    const interval = age > 60_000 ? 1500 : age > 10_000 ? 800 : pollMs;
    await sleep(interval);
    if (signal?.aborted) throw abort();
  }
}


// Exposed for dev-tool / about-dialog display only.
export async function getResolvedBaseUrl(): Promise<string> {
  return resolveBaseUrl();
}
