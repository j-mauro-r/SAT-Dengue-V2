import type { Forecast } from "./demo-data";

export function resultDetails(municipalityId: string, horizon: Forecast["horizon"]) {
  return {
    model: "XGBoost" as const,
    modelVersion: "xgb-0.3.1",
    dataVersion: "dengue-2026.10.03",
    resultId: `SAT-20261005-${municipalityId.toUpperCase()}-${horizon === "T+1" ? "01" : "02"}`,
  };
}