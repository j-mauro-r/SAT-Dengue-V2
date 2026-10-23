import { describe, expect, it } from "vitest";
import { resultDetails } from "@/lib/result-details";

describe("Forecast result provenance", () => {
  it("uses one of the requested model families", () => {
    expect(["XGBoost", "LightGBM", "GAM"]).toContain(resultDetails("ibague", "T+1").model);
  });
  it("contains exclusively the four technical fields requested", () => {
    expect(Object.keys(resultDetails("ibague", "T+1")).sort()).toEqual(["dataVersion", "model", "modelVersion", "resultId"]);
  });
  it("identifies each municipality and horizon separately and deterministically", () => {
    expect(resultDetails("ibague", "T+1").resultId).toBe("SAT-20261005-IBAGUE-01");
    expect(resultDetails("ibague", "T+2").resultId).not.toBe(resultDetails("ibague", "T+1").resultId);
    expect(resultDetails("melgar", "T+1").resultId).not.toBe(resultDetails("ibague", "T+1").resultId);
  });
});