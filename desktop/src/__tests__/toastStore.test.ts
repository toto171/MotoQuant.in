import { describe, it, expect, beforeEach, vi } from "vitest";
import { useToastStore, toast } from "@/store/toastStore";

beforeEach(() => {
  useToastStore.setState({ toasts: [] });
  vi.useFakeTimers();
});

describe("toastStore", () => {
  it("push adds a toast with default 'info' variant", () => {
    useToastStore.getState().push({ message: "Hello" });
    expect(useToastStore.getState().toasts).toHaveLength(1);
    expect(useToastStore.getState().toasts[0].variant).toBe("info");
    expect(useToastStore.getState().toasts[0].message).toBe("Hello");
  });

  it("push caps stack at 3 toasts", () => {
    for (let i = 0; i < 5; i++) {
      useToastStore.getState().push({ message: `msg ${i}` });
    }
    expect(useToastStore.getState().toasts).toHaveLength(3);
  });

  it("caps at 3 by keeping the 3 most recent", () => {
    for (let i = 0; i < 5; i++) {
      useToastStore.getState().push({ message: `msg ${i}` });
    }
    // The 3 most-recently pushed messages survive.
    const msgs = useToastStore.getState().toasts.map((t) => t.message);
    expect(msgs).toContain("msg 4");
    expect(msgs).toContain("msg 3");
    expect(msgs).toContain("msg 2");
  });

  it("dismiss removes the correct toast by id", () => {
    useToastStore.getState().push({ message: "A" });
    useToastStore.getState().push({ message: "B" });
    const id = useToastStore.getState().toasts[0].id;
    useToastStore.getState().dismiss(id);
    expect(useToastStore.getState().toasts).toHaveLength(1);
    expect(useToastStore.getState().toasts[0].message).toBe("B");
  });

  it("toast auto-dismisses after 3000 ms", () => {
    useToastStore.getState().push({ message: "Auto" });
    expect(useToastStore.getState().toasts).toHaveLength(1);
    vi.advanceTimersByTime(3100);
    expect(useToastStore.getState().toasts).toHaveLength(0);
  });

  it("convenience helpers push with correct variants", () => {
    // Clear and push one at a time so the cap doesn't evict any.
    useToastStore.setState({ toasts: [] });
    toast.success("s");
    expect(useToastStore.getState().toasts[0].variant).toBe("success");

    useToastStore.setState({ toasts: [] });
    toast.error("e");
    expect(useToastStore.getState().toasts[0].variant).toBe("error");

    useToastStore.setState({ toasts: [] });
    toast.warn("w");
    expect(useToastStore.getState().toasts[0].variant).toBe("warn");

    useToastStore.setState({ toasts: [] });
    toast.info("i");
    expect(useToastStore.getState().toasts[0].variant).toBe("info");
  });
});
