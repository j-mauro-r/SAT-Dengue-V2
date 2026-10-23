export interface DashboardConfig {
  readonly apiBaseUrl: string;
}

export class DashboardConfigError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "DashboardConfigError";
  }
}

export function parseApiBaseUrl(value: string | undefined): string {
  const candidate = value?.trim() ?? "";
  if (!candidate) return "";

  let parsed: URL;
  try {
    parsed = new URL(candidate);
  } catch {
    throw new DashboardConfigError(
      "VITE_API_BASE_URL debe ser una URL HTTP(S) absoluta o quedar vacía.",
    );
  }
  if (!(["http:", "https:"] as const).includes(parsed.protocol as "http:" | "https:")) {
    throw new DashboardConfigError("VITE_API_BASE_URL solo admite los protocolos HTTP y HTTPS.");
  }
  if (parsed.search || parsed.hash) {
    throw new DashboardConfigError("VITE_API_BASE_URL no puede contener parámetros ni fragmentos.");
  }
  return candidate.replace(/\/$/, "");
}

export const API_BASE_URL = import.meta.env["VITE_API_BASE_URL"]?.trim() ?? "";

export function getDashboardConfig(): DashboardConfig {
  return { apiBaseUrl: parseApiBaseUrl(API_BASE_URL) };
}
