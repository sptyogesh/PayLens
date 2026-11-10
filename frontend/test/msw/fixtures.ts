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
