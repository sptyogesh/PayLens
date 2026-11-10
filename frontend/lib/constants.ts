/** Every UI label, route and limit in one place (constitution Principle XIV). */

export const ROUTES = {
  home: "/",
  transactions: "/transactions",
  pay: "/pay",
} as const;

export const NAV_ITEMS = [
  { href: ROUTES.transactions, label: "Transactions" },
  { href: ROUTES.pay, label: "Pay (sandbox)" },
] as const;

export const APP_NAME = "PayLens";

export const SOURCE_LABELS = {
  paypal_sandbox: "PayPal sandbox",
  demo_seed: "Demo seed",
} as const;

export const FIRA_LABELS = {
  matched: "Matched",
  needs_review: "Needs review",
  missing: "Missing",
} as const;

export const DISCLAIMERS = {
  demoMode: "Demo mode — PayPal sandbox data",
  sandboxCheckout: "Sandbox demo — no real money moves. Use a PayPal sandbox personal account.",
  simulated: "Simulated (sandbox)",
  notTaxAdvice: "Prepared from user data — not tax advice. Confirm with a CA.",
} as const;

export const GAIN_LABEL = "Gain";

/** Must match backend app/common/constants.py. */
export const CHECKOUT_CURRENCIES = ["USD", "GBP", "EUR", "AUD"] as const;
export const CHECKOUT_DESCRIPTION_MAX = 127;
export const CHECKOUT_MAX_AMOUNT = "10000.00";

export const DISPLAY_LOCALE = "en-IN";
export const DISPLAY_TIME_ZONE = "Asia/Kolkata";

export const MESSAGES = {
  loading: "Loading…",
  genericError: "Something went wrong. Please try again.",
  invalidResponse: "The server sent data in an unexpected format.",
  networkError: "Cannot reach the PayLens server. Check that it is running.",
  retry: "Try again",
} as const;

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

export const TRANSACTIONS_TEXT = {
  title: "Transactions",
  gridLabel: "Transactions",
  emptyTitle: "No transactions yet",
  emptyMessage: "Press Sync now to fetch payments from the PayPal sandbox.",
  flagged: "Check",
  flaggedHint: "PayPal data for this payment looked unusual. It is stored as received.",
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

export const LEAKAGE_TEXT = {
  midRate: "Mid-market rate",
  paypalRate: `PayPal rate (${DISCLAIMERS.simulated})`,
  inrReceived: `INR received (${DISCLAIMERS.simulated})`,
  feeLoss: "Fee loss",
  fxLoss: `FX loss (${DISCLAIMERS.simulated})`,
  totalLeakage: "Total leakage",
  leakagePercent: "Leakage %",
  status: {
    rate_unavailable: "Rate unavailable",
    not_calculated: "Not calculated",
    not_applicable: "—",
  },
  statusHint: {
    rate_unavailable: "No exchange rate yet. It is fetched again on the next sync.",
    not_calculated: "The fee is larger than the payment, so leakage is not calculated.",
    not_applicable: "Only completed income has leakage.",
  },
  simulatedNote:
    "PayPal rate is simulated for the sandbox: the mid-market reference rate minus a fixed spread.",
} as const;
