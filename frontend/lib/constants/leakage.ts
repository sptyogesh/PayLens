import { DISCLAIMERS } from "./core";

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

/** Keys and labels must match backend app/common/periods.py. */
export const PERIOD_OPTIONS = [
  { value: "this_month", label: "This month" },
  { value: "last_3_months", label: "Last 3 months" },
  { value: "all_time", label: "All time" },
] as const;
export const DEFAULT_PERIOD: (typeof PERIOD_OPTIONS)[number]["value"] = "last_3_months";

export const DASHBOARD_TEXT = {
  title: "Leakage dashboard",
  periodLabel: "Period",
  showing: "Showing",
  cards: {
    income: "Total income (INR, mid-market)",
    feeLoss: "Fee loss",
    fxLoss: LEAKAGE_TEXT.fxLoss,
    totalLeakage: LEAKAGE_TEXT.totalLeakage,
    leakagePercent: LEAKAGE_TEXT.leakagePercent,
  },
  simulatedHint: `Includes FX loss at the ${DISCLAIMERS.simulated.toLowerCase()} rate`,
  paymentsHint: (count: number) => `${count} payment${count === 1 ? "" : "s"}`,
  noPercent: "—",
  includes: "Includes",
  excluded: (count: number) =>
    `${count} payment${count === 1 ? " is" : "s are"} not included because the exchange rate is unavailable. They are added after the next sync.`,
  notCalculated: (count: number) =>
    `${count} payment${count === 1 ? " is" : "s are"} not included because the PayPal fee is larger than the payment. Check these in Transactions.`,
  labelColumnMinWidthPx: 220,
  byMonth: "Leakage by month",
  byClient: "Leakage by client",
  columns: {
    month: "Month (IST)",
    client: "Client",
    payments: "Payments",
    income: "Income (INR)",
  },
  emptyTitle: "No payments in this period",
  emptyMessage: "Choose All time, press Sync now on the Transactions page, or load the demo seed.",
  spreadNote: (spread: string) =>
    `${DISCLAIMERS.simulated}: the PayPal rate is the mid-market reference rate minus ${spread}%. Sandbox payments have no real INR conversion.`,
} as const;
