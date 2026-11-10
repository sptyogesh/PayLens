import { CHECKOUT_DESCRIPTION_MAX, CHECKOUT_MAX_AMOUNT } from "./core";

export const SYNC_TEXT = {
  button: "Sync now",
  running: "Syncing with PayPal sandbox…",
  neverRun: "No sync has run yet. Press Sync now to fetch your PayPal sandbox payments.",
  outcome: {
    running: "Sync running",
    success: "Sync finished",
    partial: "Sync partly finished",
    failed: "Sync failed",
  },
  trigger: { manual: "manual", startup: "on startup" },
} as const;

/** Largest page GET /transactions allows. Must match backend TRANSACTIONS_PAGE_MAX. */
export const TRANSACTIONS_PAGE_MAX = 200;

export const TRANSACTIONS_TEXT = {
  title: "Transactions",
  gridLabel: "Transactions",
  emptyTitle: "No transactions yet",
  emptyMessage: "Press Sync now to fetch payments from the PayPal sandbox.",
  flagged: "Check",
  flaggedHint: "PayPal data for this payment looked unusual. It is stored as received.",
  partialList: (shown: number, total: number) =>
    `Showing ${String(shown)} of ${String(total)} transactions (newest first)`,
} as const;

export const TRANSACTION_STATUS_LABELS = {
  completed: "Completed",
  pending: "Pending",
  denied: "Denied",
  reversed: "Reversed",
} as const;

export const PAY_TEXT = {
  title: "Pay (sandbox)",
  formTitle: "Pay the freelancer",
  amountLabel: "Amount",
  currencyLabel: "Currency",
  descriptionLabel: "Description (optional)",
  fakeButton: "Pay (test mode)",
  processing: "Processing payment…",
  successTitle: "Payment received",
  transactionIdLabel: "PayPal transaction ID",
  notRecorded: "The payment went through. It will appear in PayLens after the next sync.",
  noPayment: "No payment was made.",
  errors: {
    amountFormat: "Enter an amount like 50 or 50.00 (at most 2 decimals).",
    amountMin: "The amount must be more than 0.",
    amountMax: `The amount must be at most ${CHECKOUT_MAX_AMOUNT}.`,
    description: `Use at most ${CHECKOUT_DESCRIPTION_MAX} characters.`,
  },
} as const;
