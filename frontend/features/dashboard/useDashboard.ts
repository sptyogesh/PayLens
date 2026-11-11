"use client";

import { useApi } from "@/hooks/useApi";
import type { PeriodKey } from "@/lib/api/dashboard-schemas";
import { DashboardSchema } from "@/lib/api/dashboard-schemas";

export const DASHBOARD_PATH = "/dashboard";

export function useDashboard(period: PeriodKey) {
  return useApi(`${DASHBOARD_PATH}?period=${period}`, DashboardSchema);
}
