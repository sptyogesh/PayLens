"use client";

import { useCallback, useState } from "react";

import { ApiError, apiGetBlob } from "@/lib/api/client";
import type { PeriodKey } from "@/lib/api/dashboard-schemas";
import { REPORT_PDF_PATH, REPORT_TEXT, REPORT_TIMEOUT_MS } from "@/lib/constants";
import { downloadBlob } from "@/lib/download";

export type DownloadReportState =
  { status: "idle" } | { status: "pending" } | { status: "error"; message: string };

/** Fetch the CA report PDF for `period` and hand it to the browser as a download. */
export function useDownloadReport(period: PeriodKey) {
  const [state, setState] = useState<DownloadReportState>({ status: "idle" });

  const download = useCallback(async (): Promise<void> => {
    setState({ status: "pending" });
    try {
      const path = `${REPORT_PDF_PATH}?period=${encodeURIComponent(period)}`;
      const { blob, fileName } = await apiGetBlob(path, { timeoutMs: REPORT_TIMEOUT_MS });
      downloadBlob(blob, fileName);
      setState({ status: "idle" });
    } catch (error) {
      const message = error instanceof ApiError ? error.message : REPORT_TEXT.failed;
      setState({ status: "error", message });
    }
  }, [period]);

  return { state, download };
}
