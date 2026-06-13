import { describe, it, expect } from "vitest";
import { isExclusiveCategory } from "@/pages/BuildPage";

describe("isExclusiveCategory", () => {
  it("returns true for exhaust variants", () => {
    expect(isExclusiveCategory("exhaust")).toBe(true);
    expect(isExclusiveCategory("exhaust-full-system")).toBe(true);
    expect(isExclusiveCategory("EXHAUST")).toBe(true);
  });

  it("returns true for ecu", () => {
    expect(isExclusiveCategory("ecu")).toBe(true);
    expect(isExclusiveCategory("ECU Flash")).toBe(true);
  });

  it("returns true for chain, sprockets, clutch", () => {
    expect(isExclusiveCategory("chain")).toBe(true);
    expect(isExclusiveCategory("front-sprocket")).toBe(true);
    expect(isExclusiveCategory("rear_sprocket")).toBe(true);
    expect(isExclusiveCategory("slipper")).toBe(true);
    expect(isExclusiveCategory("clutch")).toBe(true);
  });

  it("returns true for forced induction", () => {
    expect(isExclusiveCategory("turbo")).toBe(true);
    expect(isExclusiveCategory("supercharger")).toBe(true);
    expect(isExclusiveCategory("nitrous")).toBe(true);
    expect(isExclusiveCategory("boost")).toBe(true);
    expect(isExclusiveCategory("boost_kit")).toBe(true); // canonical name
  });

  it("returns true for swingarm extensions (canonical + label)", () => {
    // Regression: the old prefix list omitted swingarm, so two extensions
    // were stackable. Backend EXCLUSIVE_CATEGORIES carries swingarm_ext.
    expect(isExclusiveCategory("swingarm_ext")).toBe(true);
    expect(isExclusiveCategory("Swingarm Ext")).toBe(true);
  });

  it("matches the backend canonical category names exactly", () => {
    for (const n of [
      "exhaust", "ecu", "air_filter", "clutch_kit", "quickshifter",
      "battery", "chain", "boost_kit", "nitrous", "wheelie_bar", "swingarm_ext",
    ]) {
      expect(isExclusiveCategory(n)).toBe(true);
    }
  });

  it("returns false for additive categories", () => {
    expect(isExclusiveCategory("bodywork")).toBe(false);
    expect(isExclusiveCategory("accessories")).toBe(false);
    expect(isExclusiveCategory("lighting")).toBe(false);
    expect(isExclusiveCategory("suspension")).toBe(false);
  });

  it("returns false for null/undefined", () => {
    expect(isExclusiveCategory(null)).toBe(false);
    expect(isExclusiveCategory(undefined)).toBe(false);
    expect(isExclusiveCategory("")).toBe(false);
  });
});
