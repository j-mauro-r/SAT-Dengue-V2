import { describe, expect, it } from "vitest";
import boundaries from "@/lib/municipal-boundaries.json";

describe("Department municipal geography", () => {
  it("includes all 47 Tolima municipalities", () => {
    expect(boundaries.tolima).toHaveLength(47);
    expect(boundaries.tolima.some((a) => a.name === "San Sebastián De Mariquita")).toBe(true);
  });
  it("includes all 29 Meta municipalities with Meta's Granada", () => {
    expect(boundaries.meta).toHaveLength(29);
    expect(boundaries.meta.filter((a) => a.id === "granada")).toHaveLength(1);
  });
});
