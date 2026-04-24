import { describe, it, expect } from "vitest";
import Fuse from "fuse.js";

// Representative subset of the real bike catalog.
const BIKES = [
  { id: 1, manufacturer: "Yamaha", model: "YZF-R15 V3", year: 2019, category: "sport", displacement_cc: 155 },
  { id: 2, manufacturer: "Yamaha", model: "YZF-R15 V4", year: 2022, category: "sport", displacement_cc: 155 },
  { id: 3, manufacturer: "Kawasaki", model: "Ninja 400", year: 2023, category: "sport", displacement_cc: 399 },
  { id: 4, manufacturer: "Kawasaki", model: "Ninja ZX-10R", year: 2021, category: "sport", displacement_cc: 998 },
  { id: 5, manufacturer: "Suzuki", model: "GSX-R 1000", year: 2005, category: "sport", displacement_cc: 999 },
  { id: 6, manufacturer: "Honda", model: "CBR 250R", year: 2012, category: "sport", displacement_cc: 249 },
  { id: 7, manufacturer: "Ducati", model: "Panigale V4R", year: 2023, category: "sport", displacement_cc: 998 },
  { id: 8, manufacturer: "Royal Enfield", model: "Interceptor 650", year: 2021, category: "cruiser", displacement_cc: 648 },
];

const OPTS = {
  keys: [
    { name: "manufacturer", weight: 0.35 },
    { name: "model", weight: 0.45 },
    { name: "year", weight: 0.1 },
    { name: "category", weight: 0.1 },
  ],
  threshold: 0.35,
  includeScore: true,
  minMatchCharLength: 1,
};

describe("BikePicker fuse.js search", () => {
  const fuse = new Fuse(BIKES, OPTS);

  it("finds 'R15 V3' as first result", () => {
    const results = fuse.search("R15 V3");
    expect(results.length).toBeGreaterThan(0);
    expect(results[0].item.model).toContain("R15 V3");
  });

  it("finds 'Ninja 400' correctly", () => {
    const results = fuse.search("Ninja 400");
    expect(results.length).toBeGreaterThan(0);
    expect(results[0].item.manufacturer).toBe("Kawasaki");
    expect(results[0].item.model).toContain("400");
  });

  it("finds bikes by manufacturer 'Ducati'", () => {
    const results = fuse.search("Ducati");
    expect(results.length).toBeGreaterThan(0);
    expect(results[0].item.manufacturer).toBe("Ducati");
  });

  it("narrows 'Ninja' to Kawasaki bikes only", () => {
    const results = fuse.search("Ninja");
    const allKawasaki = results.every((r) => r.item.manufacturer === "Kawasaki");
    expect(allKawasaki).toBe(true);
  });

  it("finds 'interceptor' case-insensitively", () => {
    const results = fuse.search("interceptor");
    expect(results.length).toBeGreaterThan(0);
    expect(results[0].item.model).toContain("Interceptor");
  });

  it("returns empty array for gibberish query", () => {
    const results = fuse.search("xzqwerty12345");
    expect(results).toHaveLength(0);
  });

  it("returns scored results (score is defined and < 1)", () => {
    const results = fuse.search("GSX-R");
    expect(results[0].score).toBeDefined();
    expect(results[0].score!).toBeLessThan(1);
  });
});
