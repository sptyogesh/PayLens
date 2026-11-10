"use client";

/**
 * Parent for the dashboard (home page). Children: PeriodFilter, DownloadReportButton,
 * LeakageSummary (cards + notes) and BreakdownTables (by month, by client). Data comes from
 * useDashboard for the period.
 */
import { useState } from "react";

import { PageHeader } from "@/components/layout/PageHeader";
import { ErrorState } from "@/components/ui/ErrorState";
import { Spinner } from "@/components/ui/Spinner";
import type { PeriodKey } from "@/lib/api/dashboard-schemas";
import { DASHBOARD_TEXT, DEFAULT_PERIOD } from "@/lib/constants";

import { BreakdownTables } from "./Breakdown";
import { DownloadReportButton } from "./DownloadReport";
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
        actions={
          <div className="flex flex-wrap items-start gap-3">
            <PeriodFilter value={period} onChange={setPeriod} />
            <DownloadReportButton period={period} />
          </div>
        }
      />
      {dashboard.status === "loading" ? <Spinner /> : null}
      {dashboard.status === "error" ? (
        <ErrorState message={dashboard.error.message} onRetry={dashboard.reload} />
      ) : null}
      {dashboard.status === "success" ? (
        <div className="space-y-8">
          <LeakageSummary data={dashboard.data} />
          <BreakdownTables data={dashboard.data} />
        </div>
      ) : null}
    </>
  );
}
