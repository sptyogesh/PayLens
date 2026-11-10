/** App-wide routes, labels, disclaimers and limits (constitution Principle XIV). */

export const ROUTES = {
  dashboard: "/",
  transactions: "/transactions",
  pay: "/pay",
  chat: "/chat",
  fira: "/fira",
} as const;

export const NAV_ITEMS = [
  { href: ROUTES.dashboard, label: "Dashboard" },
  { href: ROUTES.transactions, label: "Transactions" },
  { href: ROUTES.chat, label: "Ask your money" },
  { href: ROUTES.fira, label: "FIRAs" },
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
  timeout: "The server took too long to answer. Please try again.",
  retry: "Try again",
} as const;
