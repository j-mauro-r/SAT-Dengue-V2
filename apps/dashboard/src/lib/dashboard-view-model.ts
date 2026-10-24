import boundaries from "./municipal-boundaries.json";
import type { AvailabilityStatus, DashboardResponse } from "./dashboard-contract";

export type Dept = "tolima" | "meta";
export type Zone = "Éxito" | "Seguridad" | "Alerta" | "Exceso" | "No disponible";

export interface ChannelPoint {
  month: string;
  monthFull: string;
  idx: number;
  period: string;
  p25: number | null;
  median: number | null;
  p75: number | null;
  observed: number | null;
}

export interface Forecast {
  horizon: "T+1" | "T+2";
  targetMonth: string;
  prob: number | null;
  threshold: number | null;
  available: boolean;
  alertStatus: "ALERT" | "NO_ALERT" | "UNAVAILABLE";
  availabilityStatus: AvailabilityStatus;
  availabilityLabel: string;
  availabilityReason: string | null;
  model: string | null;
  modelLabel: string | null;
  modelRole: string | null;
  modelVersion: string | null;
  procedureId: string | null;
  resultId: string | null;
  dataVersion: string;
}

export interface Muni {
  id: string;
  geometryId: string;
  name: string;
  dept: Dept;
  channel: ChannelPoint[];
  observedT: number | null;
  zoneT: Zone;
  p25: number | null;
  median: number | null;
  p75: number | null;
  t1: Forecast;
  t2: Forecast;
}

export interface HistoryRecord {
  horizon: "T+1" | "T+2";
  procedureId: string;
  periodStart: string;
  periodEnd: string;
  geography: string;
  alerts: number | null;
  falseAlerts: number | null;
  falseAlertRatio: number | null;
  onsets: number | null;
  detected: number | null;
  onsetSensitivity: number | null;
  auroc: number | null;
  ap: number | null;
  brier: number | null;
}

export interface DashboardViewModel {
  dept: Dept;
  departmentCode: "50" | "73";
  departmentName: string;
  period: string;
  periodLabel: string;
  periodMonthIndex: number;
  periodYear: number;
  generatedAt: string;
  dataUpdatedAt: string;
  dataVersion: string;
  resultSetId: string;
  governanceGate: string;
  governanceStatus: "APPROVED" | "NOT_APPROVED";
  championStatus: "SELECTED" | "NOT_SELECTED";
  limitation: string;
  demonstrativeValues: boolean;
  municipalities: Muni[];
  history: HistoryRecord[];
}

export const DEPTS: Record<Dept, string> = { tolima: "Tolima", meta: "Meta" };
export const DEPARTMENT_CODES: Record<Dept, "50" | "73"> = { tolima: "73", meta: "50" };
export const DEFAULT_PERIODS: Record<Dept, string> = { tolima: "2026-09", meta: "2026-12" };
export const MONTHS = [
  "Ene",
  "Feb",
  "Mar",
  "Abr",
  "May",
  "Jun",
  "Jul",
  "Ago",
  "Sep",
  "Oct",
  "Nov",
  "Dic",
];
export const MONTHS_FULL = [
  "Enero",
  "Febrero",
  "Marzo",
  "Abril",
  "Mayo",
  "Junio",
  "Julio",
  "Agosto",
  "Septiembre",
  "Octubre",
  "Noviembre",
  "Diciembre",
];

const ZONES = {
  EXITO: "Éxito",
  SEGURIDAD: "Seguridad",
  ALERTA: "Alerta",
  EXCESO: "Exceso",
  UNAVAILABLE: "No disponible",
} as const;

export const AVAILABILITY_LABELS: Record<AvailabilityStatus, string> = {
  AVAILABLE: "Disponible",
  INELIGIBLE: "No elegible",
  INSUFFICIENT_HISTORY: "Historia insuficiente",
  MISSING_DATA: "Datos faltantes",
  NOT_CALCULATED: "No calculado",
};

const MODEL_LABELS: Record<string, string> = {
  xgboost: "XGBoost",
  lightgbm: "LightGBM",
  gam: "GAM",
};

function formatModelName(model: string | null): string | null {
  if (model === null) return null;
  return MODEL_LABELS[model.toLowerCase()] ?? model;
}

function normalizedName(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-zA-Z0-9]/g, "")
    .toLowerCase();
}

function geometryIds(dept: Dept): Map<string, string> {
  return new Map(boundaries[dept].map((area) => [normalizedName(area.name), area.id]));
}

function formatMonth(period: string): string {
  const [year, month] = period.split("-").map(Number);
  return `${MONTHS_FULL[(month ?? 1) - 1]} ${year}`;
}

function formatTimestamp(value: string | null): string {
  if (value === null) return "No disponible";
  return new Intl.DateTimeFormat("es-CO", {
    timeZone: "America/Bogota",
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function adaptDashboardResponse(response: DashboardResponse): DashboardViewModel {
  const dept: Dept = response.department.department_code === "73" ? "tolima" : "meta";
  const ids = geometryIds(dept);
  const dataVersion = response.metadata.data_version;
  const municipalities = response.municipalities.map((municipality): Muni => {
    const forecasts = municipality.results.map((result): Forecast => ({
      horizon: result.horizon === "T1" ? "T+1" : "T+2",
      targetMonth: formatMonth(result.target_period),
      prob: result.probability,
      threshold: result.threshold,
      available: result.availability_status === "AVAILABLE",
      alertStatus: result.alert_status,
      availabilityStatus: result.availability_status,
      availabilityLabel: AVAILABILITY_LABELS[result.availability_status],
      availabilityReason: result.availability_reason,
      model: result.model_family,
      modelLabel: formatModelName(result.model_family),
      modelRole: result.model_role,
      modelVersion: result.model_version,
      procedureId: result.procedure_id,
      resultId: result.result_id,
      dataVersion,
    }));
    const t1 = forecasts.find(({ horizon }) => horizon === "T+1")!;
    const t2 = forecasts.find(({ horizon }) => horizon === "T+2")!;
    const geometryId = ids.get(normalizedName(municipality.municipality_name));
    if (!geometryId) throw new Error(`No municipal geometry for ${municipality.municipality_code}`);
    return {
      id: municipality.municipality_code,
      geometryId,
      name: municipality.municipality_name,
      dept,
      observedT: municipality.cases_t,
      zoneT: ZONES[municipality.endemic_zone_t],
      p25: municipality.p25,
      median: municipality.median,
      p75: municipality.p75,
      t1,
      t2,
      channel: municipality.endemic_channel_series.map((point) => {
        const monthIndex = Number(point.period.slice(5)) - 1;
        return {
          month: MONTHS[monthIndex]!,
          monthFull: MONTHS_FULL[monthIndex]!,
          idx: monthIndex,
          period: point.period,
          observed: point.cases,
          p25: point.p25,
          median: point.median,
          p75: point.p75,
        };
      }),
    };
  });
  const monthIndex = Number(response.metadata.reference_period.slice(5)) - 1;
  return {
    dept,
    departmentCode: response.department.department_code,
    departmentName: response.department.department_name,
    period: response.metadata.reference_period,
    periodLabel: formatMonth(response.metadata.reference_period),
    periodMonthIndex: monthIndex,
    periodYear: Number(response.metadata.reference_period.slice(0, 4)),
    generatedAt: formatTimestamp(response.metadata.generated_at),
    dataUpdatedAt: formatTimestamp(response.metadata.data_updated_at),
    dataVersion,
    resultSetId: response.metadata.result_set_id,
    governanceGate: response.governance.governance_gate,
    governanceStatus: response.governance.governance_status,
    championStatus: response.governance.champion_status,
    limitation: response.governance.limitation,
    demonstrativeValues: response.evaluation_context.demonstrative_values,
    municipalities,
    history: response.evaluation_context.evaluation_records.map((record) => ({
      horizon: record.horizon === "T1" ? "T+1" : "T+2",
      procedureId: record.procedure_id,
      periodStart: record.evaluation_period_start,
      periodEnd: record.evaluation_period_end,
      geography: record.evaluation_geography,
      auroc: record.auroc,
      ap: record.average_precision,
      brier: record.brier,
      falseAlerts: record.false_alerts,
      alerts: record.alerts_emitted,
      falseAlertRatio: record.false_alert_ratio,
      detected: record.onsets_detected,
      onsets: record.actual_onsets,
      onsetSensitivity: record.onset_sensitivity,
    })),
  };
}
