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
};

export { ApiRequestError };

// Exposed for dev-tool / about-dialog display only.
export async function getResolvedBaseUrl(): Promise<string> {
  return resolveBaseUrl();
}
