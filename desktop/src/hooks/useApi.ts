import { useQuery, useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  CompareRequest,
  CompareResponse,
  QuickSimRequest,
  QuickSimResponse,
  SimulateRequest,
  SimulateResponse,
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

export function useLeaderboard(limit = 20) {
  return useQuery({
    queryKey: ["leaderboard", limit],
    queryFn: () => api.leaderboard({ limit }),
    staleTime: 30_000, // sim_runs doesn't update often; 30s is fine
  });
}
