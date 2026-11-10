"use client";

/**
 * Parent for the dashboard (home page). Children: PeriodFilter and LeakageSummary
 * (cards + notes). Data comes from useDashboard for the chosen period.
 */
import { useState } from "react";

import { PageHeader } from "@/components/layout/PageHeader";
import { ErrorState } from "@/components/ui/ErrorState";
import { Spinner } from "@/components/ui/Spinner";
import type { PeriodKey } from "@/lib/api/dashboard-schemas";
import { DASHBOARD_TEXT, DEFAULT_PERIOD } from "@/lib/constants";

import { LeakageSummary } from "./LeakageSummary";
import { PeriodFilter } from "./PeriodFilter";
import { useDashboard } from "./useDashboard";

export function DashboardView() {
  const [period, setPeriod] = useState<PeriodKey>(DEFAULT_PERIOD);
  const dashboard = useDashboard(period);
  return (
    <>
      <PageHeader
        title={DASHBOARD_TEXT.title}
        actions={<PeriodFilter value={period} onChange={setPeriod} />}
      />
      {dashboard.status === "loading" ? <Spinner /> : null}
      {dashboard.status === "error" ? (
        <ErrorState message={dashboard.error.message} onRetry={dashboard.reload} />
      ) : null}
      {dashboard.status === "success" ? <LeakageSummary data={dashboard.data} /> : null}
    </>
  );
}
