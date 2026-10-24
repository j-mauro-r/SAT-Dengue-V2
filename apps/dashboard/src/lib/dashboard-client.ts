import {
  apiErrorResponseSchema,
  dashboardResponseSchema,
  type DashboardResponse,
} from "./dashboard-contract";
import { DashboardConfigError, getDashboardConfig, type DashboardConfig } from "./dashboard-config";

export type DashboardClientErrorKind = "http" | "network" | "contract" | "config";

export class DashboardClientError extends Error {
  readonly kind: DashboardClientErrorKind;
  readonly status: number | null;
  readonly errorCode: string | null;

  constructor(
    kind: DashboardClientErrorKind,
    message: string,
    options: { status?: number; errorCode?: string; cause?: unknown } = {},
  ) {
    super(message, { cause: options.cause });
    this.name = "DashboardClientError";
    this.kind = kind;
    this.status = options.status ?? null;
    this.errorCode = options.errorCode ?? null;
  }
}

export function buildDashboardUrl(
  config: DashboardConfig,
  departmentCode: string,
  period: string,
): string {
  const path = "/api/dashboard";
  const url = config.apiBaseUrl
    ? new URL(path, `${config.apiBaseUrl}/`)
    : new URL(path, "http://same-origin.invalid");
  url.searchParams.set("department_code", departmentCode);
  url.searchParams.set("period", period);
  return config.apiBaseUrl ? url.toString() : `${url.pathname}${url.search}`;
}

export async function fetchDashboard(
  departmentCode: string,
  period: string,
  signal?: AbortSignal,
  options: {
    config?: DashboardConfig;
    fetcher?: typeof fetch;
    timeoutMs?: number;
  } = {},
): Promise<DashboardResponse> {
  let config: DashboardConfig;
  try {
    config = options.config ?? getDashboardConfig();
  } catch (cause) {
    if (cause instanceof DashboardConfigError) {
      throw new DashboardClientError("config", cause.message, { cause });
    }
    throw cause;
  }
  const controller = new AbortController();
  const timeoutMs = options.timeoutMs ?? 10_000;
  const timeout = setTimeout(() => controller.abort("timeout"), timeoutMs);
  const abort = () => controller.abort(signal?.reason);
  signal?.addEventListener("abort", abort, { once: true });

  try {
    const response = await (options.fetcher ?? fetch)(
      buildDashboardUrl(config, departmentCode, period),
      { headers: { Accept: "application/json" }, signal: controller.signal },
    );
    let body: unknown;
    try {
      body = await response.json();
    } catch (cause) {
      throw new DashboardClientError(
        "contract",
        "El API devolvió una respuesta que no es JSON válido.",
        {
          status: response.status,
          cause,
        },
      );
    }
    if (!response.ok) {
      const apiError = apiErrorResponseSchema.safeParse(body);
      const fallback = `El API respondió con estado ${response.status}.`;
      throw new DashboardClientError(
        "http",
        apiError.success ? apiError.data.message : fallback,
        apiError.success
          ? { status: response.status, errorCode: apiError.data.error_code }
          : { status: response.status },
      );
    }
    const parsed = dashboardResponseSchema.safeParse(body);
    if (!parsed.success) {
      throw new DashboardClientError(
        "contract",
        "La respuesta del API no cumple el contrato esperado del dashboard.",
        { status: response.status, cause: parsed.error },
      );
    }
    return parsed.data;
  } catch (error) {
    if (error instanceof DashboardClientError) throw error;
    if (controller.signal.aborted && signal?.aborted) throw error;
    const message =
      controller.signal.reason === "timeout"
        ? "El API tardó demasiado en responder."
        : "No fue posible conectarse con el API del dashboard.";
    throw new DashboardClientError("network", message, { cause: error });
  } finally {
    clearTimeout(timeout);
    signal?.removeEventListener("abort", abort);
  }
}
