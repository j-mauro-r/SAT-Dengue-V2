import { useQuery } from "@tanstack/react-query";
import { fetchDashboard } from "./dashboard-client";
import { adaptDashboardResponse } from "./dashboard-view-model";

export function useDashboard(departmentCode: string, period: string) {
  return useQuery({
    queryKey: ["dashboard", departmentCode, period],
    queryFn: async ({ signal }) =>
      adaptDashboardResponse(await fetchDashboard(departmentCode, period, signal)),
    retry: false,
    staleTime: 30_000,
  });
}
