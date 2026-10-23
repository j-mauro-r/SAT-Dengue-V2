// DATOS DEMOSTRATIVOS — simulados de forma determinista y coherente.
export type Dept = "tolima" | "meta";
export type Zone = "Éxito" | "Seguridad" | "Alerta" | "Exceso";

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

export const META_INFO = {
  periodT: { year: 2026, month: 8 }, // Septiembre 2026 (0-index)
  generatedAt: "2026-10-05 07:30 (COT)",
  dataUpdatedAt: "2026-10-03 18:12 (COT)",
  procedure: "PROC-EVAL-v0.3.1 (retrospectivo)",
  modelName: "Procedimiento candidato B — clasificación binaria >P75",
};

export const THRESHOLDS: Record<Dept, { t1: number; t2: number }> = {
  tolima: { t1: 0.42, t2: 0.38 },
  meta: { t1: 0.45, t2: 0.4 },
};

interface MuniSeed {
  id: string;
  name: string;
  scale: number; // median-ish cases per month
  phase: number; // seasonal peak month
  ratioT: number; // observed/median at T
  p1: number | null;
  p2: number | null;
  x: number; // map position 0-100
  y: number;
}

const SEEDS: Record<Dept, MuniSeed[]> = {
  tolima: [
    {
      id: "ibague",
      name: "Ibagué",
      scale: 120,
      phase: 4,
      ratioT: 1.55,
      p1: 0.61,
      p2: 0.47,
      x: 48,
      y: 42,
    },
    {
      id: "espinal",
      name: "Espinal",
      scale: 45,
      phase: 5,
      ratioT: 1.18,
      p1: 0.44,
      p2: 0.33,
      x: 62,
      y: 60,
    },
    {
      id: "melgar",
      name: "Melgar",
      scale: 30,
      phase: 3,
      ratioT: 2.1,
      p1: 0.72,
      p2: 0.66,
      x: 78,
      y: 58,
    },
    {
      id: "chaparral",
      name: "Chaparral",
      scale: 22,
      phase: 6,
      ratioT: 0.62,
      p1: 0.18,
      p2: 0.22,
      x: 34,
      y: 78,
    },
    {
      id: "mariquita",
      name: "Mariquita",
      scale: 18,
      phase: 5,
      ratioT: 0.92,
      p1: 0.29,
      p2: 0.41,
      x: 56,
      y: 16,
    },
  ],
  meta: [
    {
      id: "villavicencio",
      name: "Villavicencio",
      scale: 160,
      phase: 5,
      ratioT: 1.4,
      p1: 0.58,
      p2: 0.52,
      x: 30,
      y: 22,
    },
    {
      id: "acacias",
      name: "Acacías",
      scale: 40,
      phase: 6,
      ratioT: 0.85,
      p1: 0.31,
      p2: 0.27,
      x: 26,
      y: 40,
    },
    {
      id: "granada",
      name: "Granada",
      scale: 28,
      phase: 7,
      ratioT: 1.05,
      p1: 0.47,
      p2: 0.36,
      x: 34,
      y: 66,
    },
    {
      id: "puerto-lopez",
      name: "Puerto López",
      scale: 20,
      phase: 6,
      ratioT: 2.3,
      p1: 0.69,
      p2: null,
      x: 66,
      y: 30,
    },
  ],
};

export const DEPTS: Record<Dept, string> = { tolima: "Tolima", meta: "Meta" };

export interface ChannelPoint {
  month: string;
  idx: number;
  p25: number;
  median: number;
  p75: number;
  max: number;
  observed: number | null;
}

function seasonal(m: number, phase: number) {
  return 1 + 0.45 * Math.cos(((m - phase) / 12) * 2 * Math.PI);
}
function noise(seed: string, m: number) {
  let h = 0;
  for (const c of seed) h = (h * 31 + c.charCodeAt(0)) | 0;
  const v = Math.sin(h * 0.001 + m * 12.9898) * 43758.5453;
  return v - Math.floor(v); // 0..1
}

export function zoneFor(v: number, p: ChannelPoint): Zone {
  if (v < p.p25) return "Éxito";
  if (v < p.median) return "Seguridad";
  if (v < p.p75) return "Alerta";
  return "Exceso";
}

export function channelFor(m: MuniSeed): ChannelPoint[] {
  const T = META_INFO.periodT.month;
  return MONTHS.map((month, idx) => {
    const median = Math.round(m.scale * seasonal(idx, m.phase));
    const p25 = Math.round(median * 0.7);
    const p75 = Math.round(median * 1.35);
    const max = Math.round(median * 1.8);
    let observed: number | null = null;
    if (idx < T) observed = Math.round(median * (0.75 + noise(m.id, idx) * 0.55));
    if (idx === T) observed = Math.round(median * m.ratioT);
    return { month, idx, p25, median, p75, max, observed };
  });
}

export interface Muni extends MuniSeed {
  dept: Dept;
  channel: ChannelPoint[];
  observedT: number;
  zoneT: Zone;
  t1: Forecast;
  t2: Forecast;
}
export interface Forecast {
  horizon: "T+1" | "T+2";
  targetMonth: string;
  prob: number | null;
  threshold: number;
  available: boolean;
  alert: boolean;
}

function build(dept: Dept, s: MuniSeed): Muni {
  const channel = channelFor(s);
  const T = META_INFO.periodT.month;
  const pt = channel[T]!;
  const th = THRESHOLDS[dept];
  const mk = (h: "T+1" | "T+2", off: number, prob: number | null, threshold: number): Forecast => ({
    horizon: h,
    targetMonth: `${MONTHS_FULL[(T + off) % 12]} ${META_INFO.periodT.year}`,
    prob,
    threshold,
    available: prob !== null,
    alert: prob !== null && prob >= threshold,
  });
  return {
    ...s,
    dept,
    channel,
    observedT: pt.observed!,
    zoneT: zoneFor(pt.observed!, pt),
    t1: mk("T+1", 1, s.p1, th.t1),
    t2: mk("T+2", 2, s.p2, th.t2),
  };
}

export const MUNIS: Record<Dept, Muni[]> = {
  tolima: SEEDS.tolima.map((s) => build("tolima", s)),
  meta: SEEDS.meta.map((s) => build("meta", s)),
};

// Contexto histórico (evaluación retrospectiva 2018–2024)
export const HISTORY: Record<
  Dept,
  {
    horizon: string;
    alerts: number;
    falseAlerts: number;
    onsets: number;
    detected: number;
    auroc: number;
    ap: number;
    brier: number;
  }[]
> = {
  tolima: [
    {
      horizon: "T+1",
      alerts: 58,
      falseAlerts: 21,
      onsets: 34,
      detected: 26,
      auroc: 0.78,
      ap: 0.61,
      brier: 0.17,
    },
    {
      horizon: "T+2",
      alerts: 52,
      falseAlerts: 24,
      onsets: 34,
      detected: 22,
      auroc: 0.71,
      ap: 0.52,
      brier: 0.2,
    },
  ],
  meta: [
    {
      horizon: "T+1",
      alerts: 44,
      falseAlerts: 15,
      onsets: 27,
      detected: 21,
      auroc: 0.8,
      ap: 0.64,
      brier: 0.16,
    },
    {
      horizon: "T+2",
      alerts: 40,
      falseAlerts: 18,
      onsets: 27,
      detected: 17,
      auroc: 0.73,
      ap: 0.55,
      brier: 0.19,
    },
  ],
};
export const HISTORY_SCOPE =
  "Evaluación retrospectiva ene-2018 a dic-2024 · municipios-mes del departamento";
