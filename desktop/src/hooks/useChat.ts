// React Query mutation hook for POST /api/chat.
// Follows the same pattern as useSimulate / useQuickSimulate in useApi.ts.

import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { ChatRequest, ChatResponse } from "@/types/api";

/**
 * Wraps POST /api/chat as a React Query mutation.
 *
 * Usage:
 *   const chat = useChat();
 *   chat.mutate({ query: "how fast is my K5?" });
 *   // chat.data → ChatResponse
 *   // chat.isPending → boolean
 *   // chat.isError → boolean (only on network-level errors; recoverable
 *   //               app errors live in chat.data.error instead)
 */
export function useChat() {
  return useMutation<ChatResponse, Error, ChatRequest>({
    mutationFn: (req) => api.chat(req),
  });
}
