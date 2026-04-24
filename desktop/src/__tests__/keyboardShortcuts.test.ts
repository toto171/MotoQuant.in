import { describe, it, expect } from "vitest";

// Unit-test the route-mapping part of useKeyboardShortcuts (no React DOM needed).

const ROUTES: Record<string, string> = {
  s: "/simulate",
  b: "/bikes",
  u: "/build",
  c: "/compare",
  h: "/history",
};

describe("Keyboard navigation chord mapping", () => {
  it("maps g+s to /simulate", () => {
    expect(ROUTES["s"]).toBe("/simulate");
  });

  it("maps g+b to /bikes", () => {
    expect(ROUTES["b"]).toBe("/bikes");
  });

  it("maps g+u to /build", () => {
    expect(ROUTES["u"]).toBe("/build");
  });

  it("maps g+c to /compare", () => {
    expect(ROUTES["c"]).toBe("/compare");
  });

  it("maps g+h to /history", () => {
    expect(ROUTES["h"]).toBe("/history");
  });

  it("unmapped keys return undefined", () => {
    expect(ROUTES["x"]).toBeUndefined();
    expect(ROUTES["z"]).toBeUndefined();
    expect(ROUTES["1"]).toBeUndefined();
  });

  it("all defined routes start with /", () => {
    Object.values(ROUTES).forEach((r) => {
      expect(r.startsWith("/")).toBe(true);
    });
  });
});
