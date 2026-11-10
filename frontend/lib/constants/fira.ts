/** FIRA matching (specs/004-fira-matching). Limits must match backend app/common/constants.py. */
import { FIRA_LABELS } from "./core";

export const FIRA_MAX_BYTES = 5 * 1024 * 1024;
export const FIRA_MAX_FILES = 10;
export const PDF_CONTENT_TYPE = "application/pdf";
export const PDF_EXTENSION = ".pdf";
export const PDF_ACCEPT = `${PDF_EXTENSION},${PDF_CONTENT_TYPE}`;
const BYTES_PER_MB = 1024 * 1024;

export const FILE_UPLOAD_TEXT = {
  notPdf: (name: string) => `${name} is not a PDF. Only PDF files can be uploaded.`,
  tooLarge: (name: string, maxBytes: number) =>
    `${name} is larger than ${String(maxBytes / BYTES_PER_MB)} MB.`,
  empty: (name: string) => `${name} is empty.`,
  tooMany: (max: number) => `Choose at most ${String(max)} files at a time.`,
  errorsTitle: "These files were not uploaded:",
} as const;

export const FIRA_STATUS_LABELS = {
  matched: FIRA_LABELS.matched,
  needs_review: FIRA_LABELS.needs_review,
  no_match: "No match",
} as const;

export const FIRA_OUTCOME_LABELS = {
  stored: "Stored",
  duplicate: "Duplicate",
  rejected: "Rejected",
  failed: "Failed",
} as const;

export const FIRA_TEXT = {
  title: "FIRA matching",
  explainer:
    "A FIRA (Foreign Inward Remittance Advice) is your bank's proof that a foreign payment reached India in INR. PayLens reads each FIRA and matches it to a payment by reference, amount (±1%) and date (±7 days).",
  uploadLabel: "FIRA PDFs",
  uploadHint: `PDF only, up to ${String(FIRA_MAX_BYTES / BYTES_PER_MB)} MB each, at most ${String(FIRA_MAX_FILES)} files at a time.`,
  uploading: (current: number, total: number) =>
    `Uploading ${String(current)} of ${String(total)}…`,
  resultsLabel: "Upload results",
  cards: {
    matched: FIRA_STATUS_LABELS.matched,
    needsReview: FIRA_STATUS_LABELS.needs_review,
    noMatch: FIRA_STATUS_LABELS.no_match,
    missing: "Payments missing a FIRA",
  },
  listTitle: "Uploaded FIRAs",
  listLabel: "FIRAs",
  listEmptyTitle: "No FIRAs uploaded yet",
  listEmptyMessage: "Upload your bank's FIRA PDFs to match them to your payments.",
  missingTitle: "Payments missing a FIRA",
  missingLabel: "Payments missing a FIRA",
  missingEmptyTitle: "Every payment has a FIRA",
  columns: {
    file: "File",
    reference: "Reference",
    date: "Remittance date",
    foreign: "Foreign amount",
    inr: "INR amount",
    status: "Status",
    score: "Score",
    reason: "Reason",
    payments: "Linked payments",
    paymentDate: "Date",
    client: "Client",
    paymentId: "PayPal transaction ID",
    gross: "Gross",
  },
  column: "FIRA",
  none: "—",
} as const;

/** AI extraction can be slow; one file's upload is abandoned after this. */
export const FIRA_UPLOAD_TIMEOUT_MS = 60_000;

/** The match reason is a sentence; keep its column wide enough to read. */
export const FIRA_REASON_MIN_WIDTH_PX = 200;
