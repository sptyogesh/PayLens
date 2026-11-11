"use client";

import { Button } from "@/components/ui/Button";
import { ErrorState } from "@/components/ui/ErrorState";
import type { PeriodKey } from "@/lib/api/dashboard-schemas";
import { REPORT_TEXT } from "@/lib/constants";

import { useDownloadReport } from "./useDownloadReport";

export type DownloadReportButtonProps = { period: PeriodKey };

/** "Download CA report" for the dashboard's current period, with pending and error states. */
export function DownloadReportButton({ period }: DownloadReportButtonProps) {
  const { state, download } = useDownloadReport(period);
  const pending = state.status === "pending";
  const start = (): void => {
    void download();
  };
  return (
    <div className="flex flex-col items-start gap-2">
      <Button variant="secondary" onClick={start} disabled={pending} aria-busy={pending}>
        {pending ? REPORT_TEXT.preparing : REPORT_TEXT.download}
      </Button>
      {state.status === "error" ? <ErrorState message={state.message} onRetry={start} /> : null}
    </div>
  );
}
