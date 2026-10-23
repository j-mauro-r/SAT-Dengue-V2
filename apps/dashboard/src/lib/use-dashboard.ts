import { useQuery } from "@tanstack/react-query";
import { DashboardClientError, fetchDashboard } from "./dashboard-client";
import { adaptDashboardResponse } from "./dashboard-view-model";

export function useDashboard(departmentCode: string, period: string) {
  return useQuery({
    queryKey: ["dashboard", departmentCode, period],
    queryFn: async ({ signal }) => {
      const response = await fetchDashboard(departmentCode, period, signal);
      try {
        return adaptDashboardResponse(response);
      } catch (cause) {
        throw new DashboardClientError(
          "contract",
          "La respuesta del API no coincide con las geometrías municipales del dashboard.",
          { cause },
        );
      }
    },
    retry: false,
    staleTime: 30_000,
  });
}
