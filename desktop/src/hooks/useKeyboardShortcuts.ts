// Global keyboard shortcut handler.
//
// Handles "g x" two-key navigation chords, single-key page actions,
// the "?" modal trigger, and Escape. Guards against firing when the
// user is typing in an <input>, <textarea>, or [contenteditable].

import { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";

interface Options {
  onOpenShortcuts: () => void;
  onCloseShortcuts: () => void;
  /** Page-specific single-key handlers mounted by the currently-active page. */
  pageHandlers?: Record<string, () => void>;
}

function isTypingTarget(el: EventTarget | null): boolean {
  if (!el) return false;
  const target = el as HTMLElement;
  const tag = target.tagName.toLowerCase();
  return (
    tag === "input" ||
    tag === "textarea" ||
    tag === "select" ||
    target.isContentEditable
  );
}

export function useKeyboardShortcuts({
  onOpenShortcuts,
  onCloseShortcuts,
  pageHandlers = {},
}: Options) {
  const navigate = useNavigate();
  const gPressed = useRef(false);
  const gTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Keep a ref to page handlers so the listener closure doesn't go stale.
  const pageHandlersRef = useRef(pageHandlers);
  pageHandlersRef.current = pageHandlers;

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (isTypingTarget(e.target)) return;

      // Escape — close modals / clear state.
      if (e.key === "Escape") {
        onCloseShortcuts();
        return;
      }

      // "?" — open shortcuts modal.
      if (e.key === "?" || (e.shiftKey && e.key === "/")) {
        e.preventDefault();
        onOpenShortcuts();
        return;
      }

      // "/" — focus the bike picker / search (fire a custom event; pages listen).
      if (e.key === "/") {
        e.preventDefault();
        window.dispatchEvent(new CustomEvent("mq:focus-search"));
        return;
      }

      // "g x" navigation chords.
      if (gPressed.current) {
        gPressed.current = false;
        if (gTimer.current) clearTimeout(gTimer.current);
        const routes: Record<string, string> = {
          s: "/simulate",
          b: "/bikes",
          u: "/build",
          c: "/compare",
          h: "/history",
        };
        if (routes[e.key]) {
          e.preventDefault();
          navigate(routes[e.key]);
        }
        return;
      }

      if (e.key === "g") {
        gPressed.current = true;
        // Reset after 1 s if no second key comes.
        gTimer.current = setTimeout(() => {
          gPressed.current = false;
        }, 1000);
        return;
      }

      // Page-level single-key shortcuts.
      const handler = pageHandlersRef.current[e.key];
      if (handler) {
        e.preventDefault();
        handler();
      }
    };

    window.addEventListener("keydown", handler);
    return () => {
      window.removeEventListener("keydown", handler);
      if (gTimer.current) clearTimeout(gTimer.current);
    };
  }, [navigate, onOpenShortcuts, onCloseShortcuts]);
}
