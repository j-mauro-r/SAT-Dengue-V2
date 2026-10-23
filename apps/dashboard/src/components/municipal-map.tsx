import { useState } from "react";
import type { Dept, Muni } from "@/lib/dashboard-view-model";
import boundaries from "@/lib/municipal-boundaries.json";
import { mapResult } from "@/lib/map-result";

export function MunicipalMap({
  dept,
  munis,
  selected,
  horizon,
  onSelect,
}: {
  dept: Dept;
  munis: Muni[];
  selected: string;
  horizon: "t1" | "t2";
  onSelect: (id: string) => void;
}) {
  const [hovered, setHovered] = useState<string | null>(null);
  const areas = boundaries[dept];
  const active =
    areas.find((area) => area.id === hovered) ??
    areas.find(
      (area) => munis.find((municipality) => municipality.id === selected)?.geometryId === area.id,
    );
  const info = mapResult(
    munis.find((m) => m.geometryId === active?.id),
    horizon,
  );
  return (
    <>
      <div
        className="relative h-56 w-full rounded-lg bg-muted/40"
        onMouseLeave={() => setHovered(null)}
      >
        <svg
          viewBox="0 0 1000 400"
          className="h-full w-full"
          aria-label={`Mapa municipal de ${dept === "tolima" ? "Tolima" : "Meta"}, ${horizon === "t1" ? "T+1" : "T+2"}`}
        >
          {areas.map((area) => {
            const municipality = munis.find((m) => m.geometryId === area.id);
            const result = mapResult(municipality, horizon);
            const label = `${area.name}: ${result.probability}, ${result.label}`;
            return (
              <path
                key={area.id}
                d={area.path}
                fillRule="evenodd"
                className={`municipal-area ${municipality ? "cursor-pointer" : ""}`}
                data-state={result.state}
                data-selected={municipality?.id === selected}
                role={municipality ? "button" : "img"}
                tabIndex={0}
                aria-label={label}
                aria-pressed={municipality ? municipality.id === selected : undefined}
                onMouseEnter={() => setHovered(area.id)}
                onFocus={() => setHovered(area.id)}
                onBlur={() => setHovered(null)}
                onClick={() => {
                  setHovered(area.id);
                  if (municipality) onSelect(municipality.id);
                }}
                onKeyDown={(e) => {
                  if (municipality && (e.key === "Enter" || e.key === " ")) {
                    e.preventDefault();
                    onSelect(municipality.id);
                  }
                }}
              >
                <title>{label}</title>
              </path>
            );
          })}
        </svg>
        {active && (
          <div
            className="pointer-events-none absolute bottom-2 left-2 max-w-[calc(100%-1rem)] rounded-md border border-border bg-popover px-2 py-1 text-xs text-popover-foreground shadow-sm"
            role="status"
            aria-live="polite"
          >
            <b>{active.name}</b>
            <span className="ml-2">
              {info.probability} · {info.symbol} {info.label}
            </span>
          </div>
        )}
      </div>
      <div
        className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-xs text-muted-foreground"
        aria-label="Leyenda del mapa municipal"
      >
        <span className="inline-flex items-center gap-1">
          <span className="h-2.5 w-2.5 rounded-sm bg-zone-exceso" aria-hidden />! Alerta emitida
        </span>
        <span className="inline-flex items-center gap-1">
          <span className="h-2.5 w-2.5 rounded-sm bg-zone-exito" aria-hidden />✓ Sin alerta
        </span>
        <span className="inline-flex items-center gap-1">
          <span className="h-2.5 w-2.5 rounded-sm bg-map-unavailable" aria-hidden />– No disponible
        </span>
      </div>
      <p className="mt-1 text-xs text-muted-foreground">
        Límites municipales · geoBoundaries / DANE (2020), CC BY 4.0.
      </p>
    </>
  );
}
