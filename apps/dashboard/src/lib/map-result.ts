import type { Forecast, Muni } from "./demo-data";

export function mapResult(municipality: Muni | undefined, horizon: "t1" | "t2") {
  const forecast: Forecast | undefined = municipality?.[horizon];
  if (!forecast?.available)
    return { state: "unavailable", label: "No disponible", symbol: "–", probability: "—" } as const;
  return {
    state: forecast.alert ? "alert" : "clear",
    label: forecast.alert ? "Alerta emitida" : "Sin alerta",
    symbol: forecast.alert ? "!" : "✓",
    probability: `${Math.round((forecast.prob ?? 0) * 100)} %`,
  } as const;
}
