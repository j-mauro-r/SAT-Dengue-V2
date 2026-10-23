import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  Area,
  Bar,
  BarChart,
  CartesianGrid,
  ComposedChart,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Cell,
} from "recharts";
import {
  AlertTriangle,
  ShieldOff,
  Activity,
  CalendarClock,
  Database,
  FileCode2,
  Bell,
  BellOff,
  CircleSlash,
  ChevronDown,
  Info,
  MapPinned,
  Eye,
  Copy,
  Check,
  ArrowLeft,
  RefreshCw,
} from "lucide-react";
import {
  DEPTS,
  MONTHS,
  MONTHS_FULL,
  DEFAULT_PERIODS,
  DEPARTMENT_CODES,
  type Dept,
  type Zone,
  type Forecast,
  type Muni,
  type DashboardViewModel,
} from "@/lib/dashboard-view-model";
import { Button } from "@/components/ui/button";
import { MunicipalMap } from "@/components/municipal-map";
import { useDashboard } from "@/lib/use-dashboard";
import { DashboardClientError } from "@/lib/dashboard-client";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "SAT-Dengue V2 — Prototipo de dashboard (Tolima y Meta)" },
      {
        name: "description",
        content:
          "Prototipo de solo lectura para vigilancia de dengue en Tolima y Meta: canal endémico, alertas T+1/T+2 y contexto histórico. Datos demostrativos.",
      },
      { property: "og:title", content: "SAT-Dengue V2 — Prototipo de dashboard" },
      {
        property: "og:description",
        content:
          "Canal endémico, pronósticos T+1/T+2 y gobernanza del modelo. Datos demostrativos.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Dashboard,
});

const ZONE_STYLE: Record<Zone, { cls: string; var: string; icon: string }> = {
  Éxito: {
    cls: "text-zone-exito border-zone-exito/40 bg-zone-exito/10",
    var: "var(--zone-exito)",
    icon: "▼",
  },
  Seguridad: {
    cls: "text-zone-seguridad border-zone-seguridad/40 bg-zone-seguridad/10",
    var: "var(--zone-seguridad)",
    icon: "●",
  },
  Alerta: {
    cls: "text-zone-alerta border-zone-alerta/40 bg-zone-alerta/10",
    var: "var(--zone-alerta)",
    icon: "▲",
  },
  Exceso: {
    cls: "text-zone-exceso border-zone-exceso/40 bg-zone-exceso/10",
    var: "var(--zone-exceso)",
    icon: "◆",
  },
  "No disponible": {
    cls: "text-muted-foreground border-border bg-muted",
    var: "var(--map-unavailable)",
    icon: "–",
  },
};
const pct = (v: number | null) => (v === null ? "—" : `${Math.round(v * 100)} %`);

function ZoneBadge({ zone }: { zone: Zone }) {
  const z = ZONE_STYLE[zone];
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-xs font-semibold ${z.cls}`}
    >
      <span aria-hidden>{z.icon}</span>
      {zone}
    </span>
  );
}
function AlertBadge({ f }: { f: Forecast }) {
  if (!f.available)
    return (
      <span
        className="inline-flex items-center gap-1.5 rounded-md border border-border bg-muted px-2 py-0.5 text-xs font-semibold text-muted-foreground"
        title={f.availabilityReason ?? f.availabilityStatus}
      >
        <CircleSlash className="h-3.5 w-3.5" />
        No disponible · {f.availabilityStatus}
      </span>
    );
  return f.alertStatus === "ALERT" ? (
    <span className="inline-flex items-center gap-1.5 rounded-md border border-zone-exceso/40 bg-zone-exceso/10 px-2 py-0.5 text-xs font-semibold text-zone-exceso">
      <Bell className="h-3.5 w-3.5" />
      Alerta emitida
    </span>
  ) : (
    <span className="inline-flex items-center gap-1.5 rounded-md border border-zone-exito/40 bg-zone-exito/10 px-2 py-0.5 text-xs font-semibold text-zone-exito">
      <BellOff className="h-3.5 w-3.5" />
      Sin alerta
    </span>
  );
}
function Card({
  title,
  icon,
  children,
  className = "",
  aside,
}: {
  title: string;
  icon?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  aside?: React.ReactNode;
}) {
  return (
    <section
      className={`rounded-xl border border-border bg-card p-5 shadow-sm ${className}`}
      aria-label={title}
    >
      <header className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <h2 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
          {icon}
          {title}
        </h2>
        {aside}
      </header>
      {children}
    </section>
  );
}

function useBogotaNow() {
  const [now, setNow] = useState<string>("");
  useEffect(() => {
    const fmt = () =>
      new Intl.DateTimeFormat("es-CO", {
        timeZone: "America/Bogota",
        dateStyle: "long",
        timeStyle: "short",
      }).format(new Date());
    setNow(fmt());
    const t = setInterval(() => setNow(fmt()), 30000);
    return () => clearInterval(t);
  }, []);
  return now;
}

export function Dashboard() {
  const [dept, setDept] = useState<Dept>("tolima");
  const [period, setPeriod] = useState(DEFAULT_PERIODS.tolima);
  const [muniId, setMuniId] = useState("");
  const dashboard = useDashboard(DEPARTMENT_CODES[dept], period);
  const now = useBogotaNow();

  const switchDept = (d: Dept) => {
    setDept(d);
    setPeriod(DEFAULT_PERIODS[d]);
    setMuniId("");
  };

  if (dashboard.isPending) {
    return (
      <DashboardState title="Cargando resultados" message="Consultando el API de solo lectura…" />
    );
  }
  if (dashboard.isError) {
    return <DashboardError error={dashboard.error} onRetry={() => void dashboard.refetch()} />;
  }

  const view = dashboard.data;
  const munis = view.municipalities;
  const muni = munis.find((item) => item.id === muniId) ?? munis[0]!;

  return (
    <div className="min-h-screen bg-background">
      {view.demonstrativeValues && (
        <div
          role="alert"
          className="sticky top-0 z-50 flex items-center justify-center gap-2 bg-warn px-4 py-2 text-center text-xs font-bold tracking-wider text-warn-foreground sm:text-sm"
        >
          <AlertTriangle className="h-4 w-4 shrink-0" />
          DATOS DEMOSTRATIVOS — NO USAR PARA DECISIONES OPERATIVAS
        </div>
      )}

      <header className="border-b border-border bg-card/60">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <Activity className="h-6 w-6 text-primary" />
              <h1 className="whitespace-nowrap text-2xl font-bold tracking-tight">
                SAT-Dengue <span className="text-primary">V2</span>
              </h1>
              <span className="rounded border border-border px-1.5 py-0.5 font-mono text-[10px] uppercase text-muted-foreground">
                Prototipo · solo lectura
              </span>
            </div>
            <p className="mt-1 text-sm text-muted-foreground">
              Sistema de alerta temprana · Vigilancia epidemiológica municipal
            </p>
          </div>
          <dl className="grid grid-cols-2 gap-x-6 gap-y-2 text-xs md:grid-cols-4">
            {[
              [
                <CalendarClock key="a" className="h-3.5 w-3.5" />,
                "Fecha actual (Bogotá)",
                now || "—",
              ],
              [
                <Database key="b" className="h-3.5 w-3.5" />,
                "Última actualización de datos",
                view.dataUpdatedAt,
              ],
              [
                <CalendarClock key="c" className="h-3.5 w-3.5" />,
                "Generación del resultado",
                view.generatedAt,
              ],
              [
                <FileCode2 key="d" className="h-3.5 w-3.5" />,
                "Procedimiento evaluado",
                `${muni.t1.procedureId ?? "No disponible"} / ${muni.t2.procedureId ?? "No disponible"}`,
              ],
            ].map(([ic, k, v]) => (
              <div key={k as string}>
                <dt className="flex items-center gap-1 text-muted-foreground">
                  {ic}
                  {k}
                </dt>
                <dd className="font-mono font-medium">{v}</dd>
              </div>
            ))}
          </dl>
        </div>
        <div className="mx-auto flex max-w-7xl flex-wrap items-end gap-4 px-4 pb-0">
          <div role="tablist" aria-label="Departamento" className="flex gap-1">
            {(Object.keys(DEPTS) as Dept[]).map((d) => (
              <button
                key={d}
                role="tab"
                aria-selected={dept === d}
                onClick={() => switchDept(d)}
                className={`rounded-t-lg border border-b-0 px-5 py-2.5 text-sm font-semibold transition-colors ${dept === d ? "border-border bg-background text-foreground" : "border-transparent text-muted-foreground hover:text-foreground"}`}
              >
                {DEPTS[d]}
              </button>
            ))}
          </div>
          <div className="mb-2 ml-auto flex flex-wrap items-center gap-3 text-sm">
            <label className="flex items-center gap-2">
              <span className="text-muted-foreground">Municipio</span>
              <select
                value={muni.id}
                onChange={(e) => setMuniId(e.target.value)}
                className="rounded-md border border-input bg-background px-3 py-1.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              >
                {munis.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="flex items-center gap-2 rounded-md border border-border bg-secondary px-3 py-1 text-xs">
              <span>Periodo T</span>
              <input
                type="month"
                value={period}
                onChange={(event) => {
                  setPeriod(event.target.value);
                  setMuniId("");
                }}
                className="bg-transparent font-mono font-semibold text-foreground"
                aria-label="Periodo de referencia"
              />
            </label>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl space-y-5 px-4 py-6">
        {/* 1. Gobernanza */}
        <section
          aria-label="Estado de gobernanza del modelo"
          className="rounded-xl border border-dashed border-muted-foreground/40 bg-muted/40 p-5"
        >
          <div className="flex flex-col gap-4 md:flex-row md:items-center">
            <div className="flex items-center gap-3">
              <ShieldOff className="h-8 w-8 text-muted-foreground" />
              <div>
                <p className="text-xs uppercase tracking-wide text-muted-foreground">
                  Estado de gobernanza (no es nivel de riesgo)
                </p>
                <p className="text-lg font-bold">
                  MODELO {view.governanceStatus === "APPROVED" ? "APROBADO" : "NO APROBADO"}
                </p>
              </div>
            </div>
            <div className="flex flex-wrap gap-2 font-mono text-xs">
              <span className="rounded border border-border bg-background px-2 py-1">
                {view.governanceGate}: {view.governanceStatus}
              </span>
              <span className="rounded border border-border bg-background px-2 py-1">
                Champion: {view.championStatus === "SELECTED" ? "seleccionado" : "no seleccionado"}
              </span>
            </div>
            <p className="text-sm text-muted-foreground md:ml-auto md:max-w-xl">
              {view.limitation}
            </p>
          </div>
        </section>

        {/* 2 + 3 */}
        <div className="grid gap-5 lg:grid-cols-3">
          <Card title="Situación observada actual" icon={<Eye className="h-4 w-4" />}>
            <p className="text-sm text-muted-foreground">
              {muni.name}, {view.departmentName} · Mes T: {view.periodLabel}
            </p>
            <p className="mt-3 text-5xl font-bold tabular-nums">
              {muni.observedT ?? "No disponible"}
            </p>
            <p className="text-sm text-muted-foreground">casos observados</p>
            <div className="mt-4 flex items-center gap-2 text-sm">
              Canal endémico: <ZoneBadge zone={muni.zoneT} />
            </div>
            <p className="mt-2 text-xs text-muted-foreground">
              Referencia del mes: P25 {muni.p25 ?? "No disponible"} · Mediana{" "}
              {muni.median ?? "No disponible"} · P75 {muni.p75 ?? "No disponible"}
            </p>
          </Card>
          {[muni.t1, muni.t2].map((f) => (
            <ForecastCard key={`${muni.id}-${f.horizon}`} f={f} />
          ))}
        </div>

        {/* 4 */}
        <ChannelChart muni={muni} view={view} />

        {/* 5 + 6 */}
        <div className="grid gap-5 lg:grid-cols-5">
          <TerritoryMap dept={dept} munis={munis} selected={muni.id} onSelect={setMuniId} />
          <HorizonChart muni={muni} />
        </div>

        {/* 7 */}
        <HistoryCard view={view} />

        <footer className="pb-6 pt-2 text-center text-xs text-muted-foreground">
          Prototipo de validación de presentación (PROD-04). No reemplaza el criterio del experto ni
          constituye aprobación científica.
        </footer>
      </main>
    </div>
  );
}

function DashboardState({ title, message }: { title: string; message: string }) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-4">
      <section
        className="max-w-lg rounded-xl border border-border bg-card p-8 text-center shadow-sm"
        role="status"
      >
        <RefreshCw className="mx-auto h-8 w-8 animate-spin text-primary" />
        <h1 className="mt-4 text-xl font-semibold">{title}</h1>
        <p className="mt-2 text-sm text-muted-foreground">{message}</p>
      </section>
    </main>
  );
}

function DashboardError({ error, onRetry }: { error: Error; onRetry: () => void }) {
  const clientError = error instanceof DashboardClientError ? error : null;
  const title =
    clientError?.status === 400
      ? "Parámetros inválidos"
      : clientError?.status === 404
        ? "No hay resultados para este departamento y periodo"
        : clientError?.status === 500
          ? "Error interno del API"
          : clientError?.kind === "contract"
            ? "Respuesta incompatible"
            : clientError?.kind === "config"
              ? "Configuración inválida"
              : "Error de red";
  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-4">
      <section
        className="max-w-lg rounded-xl border border-border bg-card p-8 text-center shadow-sm"
        role="alert"
      >
        <AlertTriangle className="mx-auto h-8 w-8 text-zone-alerta" />
        <h1 className="mt-4 text-xl font-semibold">{title}</h1>
        <p className="mt-2 text-sm text-muted-foreground">{error.message}</p>
        <Button className="mt-5" onClick={onRetry}>
          <RefreshCw /> Reintentar
        </Button>
      </section>
    </main>
  );
}

function ForecastCard({ f }: { f: Forecast }) {
  const [detail, setDetail] = useState(false);
  const [copyMessage, setCopyMessage] = useState("");
  const copyIdentifier = async () => {
    if (!f.resultId) return;
    try {
      await navigator.clipboard.writeText(f.resultId);
      setCopyMessage("Identificador copiado");
    } catch {
      setCopyMessage("No se pudo copiar el identificador");
    }
  };
  return (
    <Card
      title={`Pronóstico ${f.horizon}`}
      icon={<CalendarClock className="h-4 w-4" />}
      aside={
        <span className={detail ? "invisible" : ""} aria-hidden={detail}>
          <AlertBadge f={f} />
        </span>
      }
    >
      <span className="sr-only" role="status" aria-live="polite">
        {detail ? `Detalle del resultado ${f.horizon}` : `Resultado ${f.horizon}`}. {copyMessage}
      </span>
      <div className="grid">
        <div
          className={`col-start-1 row-start-1 transition-opacity duration-150 motion-reduce:transition-none ${detail ? "invisible opacity-0" : "visible opacity-100"}`}
          aria-hidden={detail}
          inert={detail}
        >
          <p className="text-sm text-muted-foreground">
            Mes objetivo: <b className="text-foreground">{f.targetMonth}</b>
          </p>
          {f.available && f.prob !== null && f.threshold !== null ? (
            <>
              <div className="mt-3 flex items-baseline gap-2">
                <span className="text-5xl font-bold tabular-nums">{pct(f.prob)}</span>
                <span className="text-sm text-muted-foreground">probabilidad estimada</span>
              </div>
              <div className="mt-4 h-2 w-full rounded-full bg-muted" aria-hidden>
                <div
                  className="relative h-2 rounded-full bg-primary"
                  style={{ width: `${f.prob * 100}%` }}
                />
                <div
                  className="relative -mt-3 h-4 w-0.5 bg-foreground"
                  style={{ marginLeft: `${f.threshold * 100}%` }}
                />
              </div>
              <p className="mt-2 text-xs text-muted-foreground">
                Umbral aplicado: <b className="text-foreground">{pct(f.threshold)}</b> · Estado:
                disponible
              </p>
            </>
          ) : (
            <p className="mt-4 text-sm text-muted-foreground">
              No disponible — {f.availabilityStatus}. {f.availabilityReason}
            </p>
          )}
          <p className="mt-3 flex gap-1.5 rounded-md bg-muted/60 p-2 text-xs text-muted-foreground">
            <Info className="mt-0.5 h-3.5 w-3.5 shrink-0" />
            Estima la probabilidad de que el mes objetivo supere el P75 histórico. No representa el
            número esperado de casos.
          </p>
        </div>
        <div
          className={`col-start-1 row-start-1 min-w-0 transition-opacity duration-150 motion-reduce:transition-none ${detail ? "visible opacity-100" : "invisible opacity-0"}`}
          aria-hidden={!detail}
          inert={!detail}
        >
          <dl className="space-y-3 text-sm">
            <div>
              <dt className="text-xs text-muted-foreground">Modelo utilizado</dt>
              <dd className="font-semibold">{f.model ?? "No disponible"}</dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">Horizonte</dt>
              <dd className="font-mono text-xs">{f.horizon}</dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">Rol del modelo</dt>
              <dd className="font-mono text-xs">{f.modelRole ?? "No disponible"}</dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">Versión del modelo</dt>
              <dd className="font-mono text-xs">{f.modelVersion ?? "No disponible"}</dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">Versión de los datos</dt>
              <dd className="font-mono text-xs">{f.dataVersion}</dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">
                Identificador del resultado generado
              </dt>
              <dd className="flex min-w-0 items-center gap-2">
                <span className="min-w-0 break-all font-mono text-xs">
                  {f.resultId ?? "No disponible"}
                </span>
                {f.resultId && (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="min-h-11 min-w-11 shrink-0"
                    aria-label="Copiar identificador del resultado"
                    title="Copiar identificador del resultado"
                    onClick={copyIdentifier}
                  >
                    {copyMessage === "Identificador copiado" ? <Check /> : <Copy />}
                  </Button>
                )}
              </dd>
            </div>
          </dl>
        </div>
      </div>
      <Button
        variant="secondary"
        size="sm"
        className="mt-4 min-h-11 border border-border"
        aria-expanded={detail}
        onClick={() => {
          setDetail(!detail);
          setCopyMessage("");
        }}
      >
        {detail && <ArrowLeft />} {detail ? "Volver al resultado" : "Detalle del resultado"}
      </Button>
    </Card>
  );
}

function ChannelChart({ muni, view }: { muni: Muni; view: DashboardViewModel }) {
  const T = view.periodMonthIndex;
  const data = muni.channel.map((p) => ({
    ...p,
    b1: p.p25,
    b2: p.median !== null && p.p25 !== null ? p.median - p.p25 : null,
    b3: p.p75 !== null && p.median !== null ? p.p75 - p.median : null,
  }));
  return (
    <Card
      title={`Canal endémico — ${muni.name}`}
      icon={<Activity className="h-4 w-4" />}
      aside={
        <ul className="flex flex-wrap gap-3 text-xs" aria-label="Leyenda">
          {(Object.keys(ZONE_STYLE) as Zone[])
            .filter((z) => z !== "No disponible")
            .map((z) => (
              <li key={z} className="flex items-center gap-1">
                <span
                  className="h-3 w-3 rounded-sm"
                  style={{ background: ZONE_STYLE[z].var, opacity: 0.6 }}
                />
                {z}
              </li>
            ))}
          <li className="flex items-center gap-1">
            <span className="h-0.5 w-4 bg-foreground" />
            Casos observados
          </li>
        </ul>
      }
    >
      <div
        className="h-80"
        role="img"
        aria-label={`Canal endémico ${muni.name} ${view.periodYear}. Mes T ${MONTHS_FULL[T]}: ${muni.observedT ?? "sin dato"} casos, zona ${muni.zoneT}.`}
      >
        <ResponsiveContainer>
          <ComposedChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
            <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" />
            <XAxis dataKey="month" stroke="var(--muted-foreground)" fontSize={12} />
            <YAxis stroke="var(--muted-foreground)" fontSize={12} />
            <ReferenceLine
              x={MONTHS[T]!}
              stroke="var(--primary)"
              strokeWidth={2}
              strokeDasharray="4 3"
              label={{
                value: "Mes T",
                fill: "var(--primary)",
                fontSize: 11,
                position: "insideTop",
              }}
            />
            <Area
              stackId="z"
              dataKey="b1"
              name="Éxito (<P25)"
              fill="var(--zone-exito)"
              fillOpacity={0.35}
              stroke="none"
            />
            <Area
              stackId="z"
              dataKey="b2"
              name="Seguridad (P25–Mediana)"
              fill="var(--zone-seguridad)"
              fillOpacity={0.3}
              stroke="none"
            />
            <Area
              stackId="z"
              dataKey="b3"
              name="Alerta (Mediana–P75)"
              fill="var(--zone-alerta)"
              fillOpacity={0.3}
              stroke="none"
            />
            <Line
              dataKey="observed"
              name="Casos observados"
              stroke="var(--foreground)"
              strokeWidth={2.5}
              dot={(props: { cx?: number; cy?: number; index?: number; value?: number | null }) =>
                props.value == null ? (
                  <g key={props.index} />
                ) : (
                  <circle
                    key={props.index}
                    cx={props.cx}
                    cy={props.cy}
                    r={props.index === T ? 6 : 3}
                    fill={props.index === T ? "var(--primary)" : "var(--foreground)"}
                  />
                )
              }
              connectNulls={false}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (!active || !payload?.length) return null;
                const p = payload[0]!.payload as (typeof data)[number];
                return (
                  <div className="rounded-md border border-border bg-popover p-2 text-xs text-popover-foreground shadow">
                    <p className="font-semibold">
                      {MONTHS_FULL[p.idx]}
                      {p.idx === T ? " (Mes T)" : ""}
                    </p>
                    <p>Observados: {p.observed ?? "sin dato"}</p>
                    <p>
                      P25 {p.p25} · Mediana {p.median} · P75 {p.p75}
                    </p>
                  </div>
                );
              }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}

function TerritoryMap({
  dept,
  munis,
  selected,
  onSelect,
}: {
  dept: Dept;
  munis: Muni[];
  selected: string;
  onSelect: (id: string) => void;
}) {
  const [h, setH] = useState<"t1" | "t2">("t1");
  return (
    <Card
      title={`Representación territorial — ${DEPTS[dept]}`}
      icon={<MapPinned className="h-4 w-4" />}
      className="lg:col-span-3"
      aside={
        <div
          role="group"
          aria-label="Horizonte del mapa"
          className="flex rounded-md border border-border p-0.5 text-xs"
        >
          {(["t1", "t2"] as const).map((k) => (
            <Button
              key={k}
              variant="ghost"
              size="sm"
              aria-pressed={h === k}
              onClick={() => setH(k)}
              className={`h-auto rounded px-3 py-1 font-semibold ${h === k ? "bg-primary text-primary-foreground" : "text-muted-foreground"}`}
            >
              {k === "t1" ? "T+1" : "T+2"}
            </Button>
          ))}
        </div>
      }
    >
      <MunicipalMap
        key={dept}
        dept={dept}
        munis={munis}
        selected={selected}
        horizon={h}
        onSelect={onSelect}
      />
      <div className="mt-3 overflow-x-auto">
        <table className="w-full text-left text-xs">
          <caption className="sr-only">
            Tabla equivalente al mapa: estado observado y riesgo T+1/T+2 por municipio
          </caption>
          <thead className="text-muted-foreground">
            <tr className="border-b border-border">
              <th className="py-2 pr-2">Municipio</th>
              <th className="pr-2">Casos T</th>
              <th className="pr-2">Estado observado</th>
              <th className="pr-2">T+1</th>
              <th>T+2</th>
            </tr>
          </thead>
          <tbody>
            {munis.map((m) => (
              <tr
                key={m.id}
                className={`border-b border-border/60 ${m.id === selected ? "bg-accent/50" : ""}`}
              >
                <td className="py-2 pr-2">
                  <button className="font-medium hover:text-primary" onClick={() => onSelect(m.id)}>
                    {m.name}
                  </button>
                </td>
                <td className="pr-2 tabular-nums">{m.observedT ?? "No disponible"}</td>
                <td className="pr-2">
                  <ZoneBadge zone={m.zoneT} />
                </td>
                <td className="pr-2">
                  <span className="mr-1 tabular-nums">{pct(m.t1.prob)}</span>
                  <AlertBadge f={m.t1} />
                </td>
                <td>
                  <span className="mr-1 tabular-nums">{pct(m.t2.prob)}</span>
                  <AlertBadge f={m.t2} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

function HorizonChart({ muni }: { muni: Muni }) {
  const data = [muni.t1, muni.t2].map((f) => ({
    name: `${f.horizon} · ${f.targetMonth.split(" ")[0]}`,
    prob: f.prob,
    th: f.threshold,
    f,
  }));
  return (
    <Card
      title="Comparación de horizontes"
      icon={<Activity className="h-4 w-4" />}
      className="lg:col-span-2"
    >
      <p className="mb-2 text-xs text-muted-foreground">
        {muni.name}: probabilidad estimada de superar P75 frente al umbral de cada horizonte (línea
        punteada).
      </p>
      <div className="h-56">
        <ResponsiveContainer>
          <BarChart data={data} layout="vertical" margin={{ left: 10, right: 20 }}>
            <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" horizontal={false} />
            <XAxis
              type="number"
              domain={[0, 1]}
              tickFormatter={(v) => `${v * 100}%`}
              stroke="var(--muted-foreground)"
              fontSize={11}
            />
            <YAxis
              type="category"
              dataKey="name"
              width={90}
              stroke="var(--muted-foreground)"
              fontSize={11}
            />
            <Bar dataKey="prob" barSize={26} radius={4}>
              {data.map((d) => (
                <Cell
                  key={d.name}
                  fill={
                    !d.f.available
                      ? "var(--muted)"
                      : d.f.alertStatus === "ALERT"
                        ? "var(--zone-exceso)"
                        : "var(--primary)"
                  }
                />
              ))}
            </Bar>
            {muni.t1.threshold !== null && (
              <ReferenceLine
                x={muni.t1.threshold}
                stroke="var(--foreground)"
                strokeDasharray="4 3"
                label={{
                  value: `U T+1 ${pct(muni.t1.threshold)}`,
                  fill: "var(--muted-foreground)",
                  fontSize: 10,
                  position: "top",
                }}
              />
            )}
            {muni.t2.threshold !== null && muni.t2.threshold !== muni.t1.threshold && (
              <ReferenceLine
                x={muni.t2.threshold}
                stroke="var(--muted-foreground)"
                strokeDasharray="2 3"
                label={{
                  value: `U T+2 ${pct(muni.t2.threshold)}`,
                  fill: "var(--muted-foreground)",
                  fontSize: 10,
                  position: "bottom",
                }}
              />
            )}
          </BarChart>
        </ResponsiveContainer>
      </div>
      <ul className="mt-2 space-y-1 text-xs">
        {[muni.t1, muni.t2].map((f) => (
          <li key={f.horizon} className="flex items-center justify-between gap-2">
            <span>
              {f.horizon}: {pct(f.prob)} vs umbral {pct(f.threshold)}
            </span>
            <AlertBadge f={f} />
          </li>
        ))}
      </ul>
    </Card>
  );
}

function HistoryCard({ view }: { view: DashboardViewModel }) {
  const rows = view.history;
  const [open, setOpen] = useState(false);
  return (
    <Card title="Contexto histórico del modelo" icon={<Database className="h-4 w-4" />}>
      <p className="mb-4 text-xs text-muted-foreground">
        {rows[0]
          ? `Evaluación ${rows[0].periodStart} a ${rows[0].periodEnd} · ${rows[0].geography}`
          : "No evaluado"}
      </p>
      <div className="grid gap-4 md:grid-cols-2">
        {rows.map((r) => (
          <div key={r.horizon} className="rounded-lg border border-border bg-background/50 p-4">
            <p className="mb-3 font-semibold">Horizonte {r.horizon}</p>
            <dl className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <dt className="text-xs text-muted-foreground">Falsas alertas / alertas emitidas</dt>
                <dd className="font-mono text-lg">
                  {r.falseAlerts ?? "No evaluado"} / {r.alerts ?? "No evaluado"}
                </dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground">% falsas alertas</dt>
                <dd className="font-mono text-lg">{pct(r.falseAlertRatio)}</dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground">
                  Inicios detectados / inicios reales
                </dt>
                <dd className="font-mono text-lg">
                  {r.detected ?? "No evaluado"} / {r.onsets ?? "No evaluado"}
                </dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground">Sensibilidad de detección</dt>
                <dd className="font-mono text-lg">{pct(r.onsetSensitivity)}</dd>
              </div>
            </dl>
          </div>
        ))}
      </div>
      <p className="mt-4 flex gap-1.5 text-xs text-muted-foreground">
        <Info className="mt-0.5 h-3.5 w-3.5 shrink-0" />
        Estos indicadores describen el comportamiento histórico del procedimiento. No determinan si
        la alerta actual será verdadera o falsa.
      </p>
      <div className="mt-4 rounded-lg border border-border">
        <button
          aria-expanded={open}
          onClick={() => setOpen(!open)}
          className="flex w-full items-center justify-between px-4 py-3 text-sm font-semibold"
        >
          Detalles técnicos{" "}
          <ChevronDown className={`h-4 w-4 transition-transform ${open ? "rotate-180" : ""}`} />
        </button>
        {open && (
          <table className="w-full border-t border-border text-left text-sm">
            <thead className="text-xs text-muted-foreground">
              <tr>
                <th className="px-4 py-2">Horizonte</th>
                <th>AUROC</th>
                <th>AP</th>
                <th>Brier</th>
              </tr>
            </thead>
            <tbody className="font-mono">
              {rows.map((r) => (
                <tr key={r.horizon} className="border-t border-border/60">
                  <td className="px-4 py-2">{r.horizon}</td>
                  <td>{r.auroc?.toFixed(2) ?? "No evaluado"}</td>
                  <td>{r.ap?.toFixed(2) ?? "No evaluado"}</td>
                  <td>{r.brier?.toFixed(2) ?? "No evaluado"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </Card>
  );
}
