import { describe, expect, it } from "vitest";
import { MUNIS } from "@/lib/demo-data";
import { mapResult } from "@/lib/map-result";

describe("Municipal map horizon states", () => {
  it("shows an emitted alert as alert", () => {
    expect(mapResult(MUNIS.tolima.find(m => m.id === "ibague"), "t1")).toEqual({ state: "alert", label: "Alerta emitida", symbol: "!", probability: "61 %" });
  });
  it("updates Espinal from alert to no alert when the horizon changes", () => {
    const espinal = MUNIS.tolima.find(m => m.id === "espinal");
    expect(mapResult(espinal, "t1").state).toBe("alert");
    expect(mapResult(espinal, "t2").state).toBe("clear");
  });
  it("shows Puerto López T+2 as unavailable without inventing a probability", () => {
    expect(mapResult(MUNIS.meta.find(m => m.id === "puerto-lopez"), "t2")).toEqual({ state: "unavailable", label: "No disponible", symbol: "–", probability: "—" });
  });
  it("shows unavailable when a municipal result does not exist", () => {
    expect(mapResult(undefined, "t1").state).toBe("unavailable");
  });
});