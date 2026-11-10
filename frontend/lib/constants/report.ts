/** CA report download (specs/005-ca-report). Must match backend report routes. */

export const REPORT_PDF_PATH = "/report.pdf";
export const REPORT_TIMEOUT_MS = 60_000;
export const DOWNLOAD_FALLBACK_FILE_NAME = "paylens-ca-report.pdf";
export const OBJECT_URL_REVOKE_DELAY_MS = 1_000;

export const REPORT_TEXT = {
  download: "Download CA report",
  preparing: "Preparing report…",
  failed: "Could not prepare the CA report. Please try again.",
} as const;
