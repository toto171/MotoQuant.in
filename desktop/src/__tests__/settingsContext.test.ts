import { describe, it, expect } from "vitest";

// Unit-test the pure conversion math without React context overhead.

const kmhToMph = (kmh: number) => kmh * 0.6214;
const kgToLb = (kg: number) => kg * 2.2046;
const nmToFtLb = (nm: number) => nm * 0.7376;

describe("Settings unit conversions", () => {
  it("converts km/h to mph correctly for a typical trap speed", () => {
    const result = kmhToMph(230);
    expect(result).toBeCloseTo(142.92, 1);
  });

  it("converts kg to lb", () => {
    expect(kgToLb(180)).toBeCloseTo(396.83, 1);
  });

  it("converts Nm to ft·lb", () => {
    expect(nmToFtLb(100)).toBeCloseTo(73.76, 1);
  });

  it("rounds to expected decimal places (1 dp trap speed)", () => {
    const val = kmhToMph(193.12).toFixed(1);
    expect(val).toBe("120.0");
  });

  it("zero values stay zero", () => {
    expect(kmhToMph(0)).toBe(0);
    expect(kgToLb(0)).toBe(0);
    expect(nmToFtLb(0)).toBe(0);
  });
});
