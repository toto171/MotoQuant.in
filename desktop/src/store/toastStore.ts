// Lightweight toast store backed by Zustand.
// Usage:
//   const toast = useToastStore((s) => s.push);
//   toast({ message: "Saved!", variant: "success" });
//
// Toasts auto-dismiss after 3 s, stack max 3. The oldest one is evicted when
// a 4th arrives before any dismissal fires.

import { create } from "zustand";

export type ToastVariant = "success" | "error" | "warn" | "info";

export interface Toast {
  id: string;
  message: string;
  variant: ToastVariant;
}

interface ToastStore {
  toasts: Toast[];
  push: (opts: { message: string; variant?: ToastVariant }) => void;
  dismiss: (id: string) => void;
}

let seq = 0;

export const useToastStore = create<ToastStore>((set) => ({
  toasts: [],
  push({ message, variant = "info" }) {
    const id = `toast-${++seq}`;
    set((s) => ({
      toasts: [...s.toasts.slice(-2), { id, message, variant }], // max 3
    }));
    setTimeout(() => {
      set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }));
    }, 3000);
  },
  dismiss(id) {
    set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }));
  },
}));

/** Convenience helpers — use in non-React code without hook rules. */
export const toast = {
  success: (message: string) =>
    useToastStore.getState().push({ message, variant: "success" }),
  error: (message: string) =>
    useToastStore.getState().push({ message, variant: "error" }),
  warn: (message: string) =>
    useToastStore.getState().push({ message, variant: "warn" }),
  info: (message: string) =>
    useToastStore.getState().push({ message, variant: "info" }),
};
