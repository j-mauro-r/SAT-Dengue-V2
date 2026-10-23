import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { afterEach, describe, expect, it, vi } from "vitest";
import { Dashboard } from "@/routes/index";
import { buildDashboardUrl, fetchDashboard } from "@/lib/dashboard-client";
import { dashboardResponseSchema, type DashboardResponse } from "@/lib/dashboard-contract";
import { adaptDashboardResponse } from "@/lib/dashboard-view-model";

const repoRoot = resolve(import.meta.dirname, "../../../..");
const fixture = (name: "tolima" | "meta"): unknown =>
  JSON.parse(
    readFileSync(
      resolve(repoRoot, `scripts/read_only_api/fixtures/dashboard_${name}.json`),
      "utf8",
    ),
  );
const response = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });

afterEach(() => vi.unstubAllGlobals());

describe("Stage 7 dashboard contract and adapter", () => {
  it("accepts both real contract fixtures and exposes all 76 municipalities", () => {
    const tolima = adaptDashboardResponse(dashboardResponseSchema.parse(fixture("tolima")));
    const meta = adaptDashboardResponse(dashboardResponseSchema.parse(fixture("meta")));

    expect(tolima.municipalities).toHaveLength(47);
    expect(meta.municipalities).toHaveLength(29);
    expect(
      new Set([...tolima.municipalities, ...meta.municipalities].map((item) => item.geometryId))
        .size,
    ).toBe(76);
  });

  it("rejects an incompatible response", () => {
    const invalid = structuredClone(fixture("tolima")) as Record<string, unknown>;
    delete invalid["governance"];
    expect(dashboardResponseSchema.safeParse(invalid).success).toBe(false);
  });

  it("passes API alerts, absences, endemic series, and individual result IDs through unchanged", () => {
    const parsed = dashboardResponseSchema.parse(fixture("tolima"));
    const view = adaptDashboardResponse(parsed);
    const ibague = view.municipalities.find(({ id }) => id === "73001")!;
    const unavailable = view.municipalities.find(
      ({ t1 }) => t1.availabilityStatus === "MISSING_DATA",
    )!;

    expect(ibague.t1.alertStatus).toBe(parsed.municipalities[0]!.results[0]!.alert_status);
    expect(ibague.t1.resultId).toBe(parsed.municipalities[0]!.results[0]!.result_id);
    expect(ibague.channel.map(({ observed }) => observed)).toEqual(
      parsed.municipalities[0]!.endemic_channel_series.map(({ cases }) => cases),
    );
    expect(unavailable.t1.prob).toBeNull();
    expect(unavailable.t1.threshold).toBeNull();
    expect(unavailable.t1.resultId).toBeNull();

    const adapterOnly = structuredClone(parsed) as DashboardResponse;
    adapterOnly.municipalities[0]!.results[0]!.alert_status = "NO_ALERT";
    expect(adaptDashboardResponse(adapterOnly).municipalities[0]!.t1.alertStatus).toBe("NO_ALERT");
  });

  it("represents all five availability states", () => {
    const views = ["tolima", "meta"].map((name) =>
      adaptDashboardResponse(dashboardResponseSchema.parse(fixture(name as "tolima" | "meta"))),
    );
    const states = new Set(
      views.flatMap(({ municipalities }) =>
        municipalities.flatMap(({ t1, t2 }) => [t1.availabilityStatus, t2.availabilityStatus]),
      ),
    );
    expect(states).toEqual(
      new Set([
        "AVAILABLE",
        "INELIGIBLE",
        "INSUFFICIENT_HISTORY",
        "MISSING_DATA",
        "NOT_CALCULATED",
      ]),
    );
  });
});

describe("typed dashboard client", () => {
  it("builds and encodes the exact endpoint query", () => {
    expect(
      buildDashboardUrl({ apiBaseUrl: "https://api.example.test/base" }, "73 &", "2026-09"),
    ).toBe("https://api.example.test/api/dashboard?department_code=73+%26&period=2026-09");
  });

  it.each([
    [400, "INVALID_PERIOD_FORMAT"],
    [404, "DASHBOARD_DATA_NOT_FOUND"],
    [500, "INTERNAL_ERROR"],
  ])("classifies contracted HTTP %i responses", async (status, errorCode) => {
    await expect(
      fetchDashboard("73", "bad", undefined, {
        config: { apiBaseUrl: "" },
        fetcher: vi.fn(async () =>
          response({ error_code: errorCode, message: "contracted" }, status),
        ),
      }),
    ).rejects.toMatchObject({ kind: "http", status, errorCode });
  });

  it("distinguishes network and contract failures", async () => {
    await expect(
      fetchDashboard("73", "2026-09", undefined, {
        config: { apiBaseUrl: "" },
        fetcher: vi.fn(async () => {
          throw new TypeError("offline");
        }),
      }),
    ).rejects.toMatchObject({ kind: "network" });
    await expect(
      fetchDashboard("73", "2026-09", undefined, {
        config: { apiBaseUrl: "" },
        fetcher: vi.fn(async () => response({ unexpected: true })),
      }),
    ).rejects.toMatchObject({ kind: "contract" });
  });
});

describe("dashboard query integration", () => {
  function renderDashboard() {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    return render(
      <QueryClientProvider client={client}>
        <Dashboard />
      </QueryClientProvider>,
    );
  }

  it("loads Tolima, switches municipality coherently, then loads Meta", async () => {
    const fetcher = vi.fn(async (input: RequestInfo | URL) =>
      response(String(input).includes("department_code=50") ? fixture("meta") : fixture("tolima")),
    );
    vi.stubGlobal("fetch", fetcher);
    renderDashboard();

    expect(await screen.findByText("Ibagué, Tolima", { exact: false })).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Municipio"), { target: { value: "73024" } });
    expect(await screen.findByText("Alpujarra, Tolima", { exact: false })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("tab", { name: "Meta" }));
    expect(await screen.findByText("Villavicencio, Meta", { exact: false })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "T+2" }));
    expect(screen.getByLabelText("Mapa municipal de Meta, T+2")).toBeInTheDocument();
  });

  it.each([
    [400, "INVALID_PERIOD_FORMAT", "Parámetros inválidos"],
    [404, "DASHBOARD_DATA_NOT_FOUND", "No hay resultados para este departamento y periodo"],
    [500, "INTERNAL_ERROR", "Error interno del API"],
  ])("renders the %i API state without prior results", async (status, errorCode, title) => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => response({ error_code: errorCode, message: "Falla controlada" }, status)),
    );
    renderDashboard();
    expect(await screen.findByText(title)).toBeInTheDocument();
    expect(screen.queryByText("Ibagué, Tolima", { exact: false })).not.toBeInTheDocument();
  });

  it.each([
    [
      "network",
      vi.fn(async () => {
        throw new TypeError("offline");
      }),
      "Error de red",
    ],
    ["contract", vi.fn(async () => response({ unexpected: true })), "Respuesta incompatible"],
  ])("renders a %s failure explicitly", async (_kind, fetcher, title) => {
    vi.stubGlobal("fetch", fetcher);
    renderDashboard();
    expect(await screen.findByText(title)).toBeInTheDocument();
  });

  it("hides prior data on error and retries manually", async () => {
    const fetcher = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(
        response({ error_code: "INTERNAL_ERROR", message: "Falla controlada" }, 500),
      )
      .mockResolvedValueOnce(response(fixture("tolima")));
    vi.stubGlobal("fetch", fetcher);
    renderDashboard();

    expect(await screen.findByText("Error interno del API")).toBeInTheDocument();
    expect(screen.queryByText("Ibagué, Tolima", { exact: false })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Reintentar/i }));
    await waitFor(() =>
      expect(screen.getByText("Ibagué, Tolima", { exact: false })).toBeInTheDocument(),
    );
    expect(fetcher).toHaveBeenCalledTimes(2);
  });
});
