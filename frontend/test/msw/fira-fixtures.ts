/** FIRA fixtures (specs/004-fira-matching), re-exported from ./fixtures. */
import type {
  FiraItem,
  FiraList,
  FiraSummary,
  FiraUploadOut,
  FiraUploadResult,
  MissingPayment,
} from "@/lib/api/fira-schemas";

const inr = (amount: string) => ({ amount, currency: "INR" });

export function firaSummary(overrides: Partial<FiraSummary> = {}): FiraSummary {
  return { matched: 1, needs_review: 1, no_match: 0, missing_payments: 1, ...overrides };
}

export function firaItem(overrides: Partial<FiraItem> = {}): FiraItem {
  return {
    id: "f-1",
    file_name: "fira-SEED-0001.pdf",
    status: "matched",
    score: 100,
    reason: null,
    foreign_amount: { amount: "100.00", currency: "USD" },
    inr_amount: inr("8400.00"),
    rate: "84.000000",
    remittance_date: "2026-11-11",
    reference_no: "3C679366HH908993F",
    remitter: "Ava Stone",
    purpose_code: "P0802",
    uploaded_at: "2026-11-11T06:30:00Z",
    matches: [
      {
        transaction_id: "t-1",
        paypal_transaction_id: "3C679366HH908993F",
        score: 100,
        kind: "direct",
      },
    ],
    ...overrides,
  };
}

export function missingPayment(overrides: Partial<MissingPayment> = {}): MissingPayment {
  return {
    transaction_id: "t-9",
    paypal_transaction_id: "SEED-0022",
    date: "2026-10-20",
    client: "Ben Hart",
    gross: { amount: "250.00", currency: "GBP" },
    ...overrides,
  };
}

export function firaList(overrides: Partial<FiraList> = {}): FiraList {
  return {
    summary: firaSummary(),
    items: [
      firaItem(),
      firaItem({
        id: "f-2",
        file_name: "fira-SEED-0020.pdf",
        status: "needs_review",
        score: 75,
        reason: "Amount differs by more than 1%",
        reference_no: "SEED-0020",
        matches: [
          { transaction_id: "t-2", paypal_transaction_id: "SEED-0020", score: 75, kind: "direct" },
        ],
      }),
    ],
    missing: [missingPayment()],
    ...overrides,
  };
}

export function firaUploadResult(overrides: Partial<FiraUploadResult> = {}): FiraUploadResult {
  return {
    file_name: "fira-SEED-0001.pdf",
    outcome: "stored",
    message: "Read and matched.",
    fira_id: "f-1",
    status: "matched",
    ...overrides,
  };
}

export function firaUploadOut(result: Partial<FiraUploadResult> = {}): FiraUploadOut {
  return { result: firaUploadResult(result), summary: firaSummary() };
}
