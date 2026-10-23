import type { Forecast, Muni } from "./dashboard-view-model";

export function mapResult(municipality: Muni | undefined, horizon: "t1" | "t2") {
  const forecast: Forecast | undefined = municipality?.[horizon];
  if (!forecast?.available)
    return {
      state: "unavailable",
      label: forecast
        ? `No disponible — ${forecast.availabilityStatus}: ${forecast.availabilityReason}`
        : "No disponible",
      symbol: "–",
      probability: "—",
    } as const;
  return {
    state: forecast.alertStatus === "ALERT" ? "alert" : "clear",
    label: forecast.alertStatus === "ALERT" ? "Alerta emitida" : "Sin alerta",
    symbol: forecast.alertStatus === "ALERT" ? "!" : "✓",
    probability: forecast.prob === null ? "—" : `${Math.round(forecast.prob * 100)} %`,
  } as const;
}
