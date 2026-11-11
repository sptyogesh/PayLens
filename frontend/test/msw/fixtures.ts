import type { ChatOut } from "@/lib/api/chat-schemas";
import type { BreakdownRow, Dashboard, Totals } from "@/lib/api/dashboard-schemas";
import type { CaptureOut, Leakage, SyncRun, Transaction, TransactionList } from "@/lib/api/schemas";

export function syncRun(overrides: Partial<SyncRun> = {}): SyncRun {
  return {
    id: "run-1",
    trigger: "manual",
    period: { start: "2026-08-12T12:00:00Z", end: "2026-11-10T12:00:00Z" },
    started_at: "2026-11-10T12:00:00Z",
    finished_at: "2026-11-10T12:00:05Z",
    outcome: "success",
    windows: { total: 3, done: 3 },
    counts: { added: 10, updated: 0, skipped: 2, flagged: 0 },
    error: null,
    hint: null,
    ...overrides,
  };
}

const inr = (amount: string) => ({ amount, currency: "INR" });

/** 100.00 USD, fee 4.70, mid 84.000000, simulated 81.480000 (values from the backend engine). */
export function leakage(overrides: Partial<Leakage> = {}): Leakage {
  return {
    mid_market_rate: "84.000000",
    paypal_rate: "81.480000",
    paypal_rate_simulated: true,
    ideal_inr: inr("8400.00"),
    inr_received: inr("7765.04"),
    fee_loss_inr: inr("394.80"),
    fx_loss_inr: inr("240.16"),
    total_leakage_inr: inr("634.96"),
    leakage_percent: "7.56",
    ...overrides,
  };
}

export function transaction(overrides: Partial<Transaction> = {}): Transaction {
  return {
    id: "t-1",
    paypal_transaction_id: "3C679366HH908993F",
    occurred_at: "2026-11-10T06:30:00Z",
    client: { id: "c-1", name: "Ava Stone", country: "US" },
    kind: "income",
    status: "completed",
    gross: { amount: "100.00", currency: "USD" },
    fee: { amount: "4.70", currency: "USD" },
    net: { amount: "95.30", currency: "USD" },
    source: "paypal_sandbox",
    is_flagged: false,
    leakage_status: "calculated",
    leakage: leakage(),
    fira_status: null,
    ...overrides,
  };
}

export function transactionList(items: Transaction[] = [transaction()]): TransactionList {
  return { items, total: items.length, limit: 100, offset: 0 };
}

export function captureOut(overrides: Partial<CaptureOut> = {}): CaptureOut {
  return {
    transaction_id: "3C679366HH908993F",
    order_id: "ORDER1",
    status: "completed",
    gross: { amount: "50.00", currency: "USD" },
    recorded: true,
    ...overrides,
  };
}

export function totals(overrides: Partial<Totals> = {}): Totals {
  return {
    payment_count: 2,
    income_inr: inr("16800.00"),
    fee_loss_inr: inr("789.60"),
    fx_loss_inr: inr("480.32"),
    total_leakage_inr: inr("1269.92"),
    leakage_percent: "7.56",
    ...overrides,
  };
}

export function breakdownRow(key: string, label: string, rowTotals = totals()): BreakdownRow {
  return { key, label, totals: rowTotals };
}

export function dashboard(overrides: Partial<Dashboard> = {}): Dashboard {
  return {
    period: {
      key: "last_3_months",
      label: "Last 3 months",
      start: "2026-08-31T18:30:00Z",
      end: "2026-11-10T09:00:00Z",
    },
    totals: totals(),
    excluded_count: 0,
    not_calculated_count: 0,
    sources: ["demo_seed", "paypal_sandbox"],
    paypal_rate_simulated: true,
    simulated_spread_percent: "3.00",
    by_month: [breakdownRow("2026-11", "Nov 2026")],
    by_client: [breakdownRow("c-1", "Ava Stone")],
    ...overrides,
  };
}

const LAST_QUARTER = "Last quarter (1 Jul 2026 – 30 Sep 2026)";

export function chatAnswer(overrides: Partial<ChatOut> = {}): ChatOut {
  return {
    answer: "Your FX loss in last quarter was ₹38,000.00 (INR, Simulated (sandbox) rate).",
    outcome: "answered",
    periods: [LAST_QUARTER],
    figures: [
      { label: "FX loss", kind: "money", value: "38000.00", currency: "INR", period: LAST_QUARTER },
      { label: "Payments", kind: "count", value: "18", currency: null, period: LAST_QUARTER },
      { label: "Leakage %", kind: "percent", value: "7.30", currency: null, period: LAST_QUARTER },
    ],
    disclaimer: null,
    tools_used: ["fee_summary"],
    ...overrides,
  };
}

export * from "./fira-fixtures";
