/** Runtime validation for API data (constitution Principle IV). Money is always a string. */
import { z } from "zod";

export const MoneySchema = z.object({
  amount: z.string().regex(/^-?\d+\.\d{2}$/, "money must be a 2-decimal string"),
  currency: z.string().regex(/^[A-Z]{3}$/),
});
export type Money = z.infer<typeof MoneySchema>;

export const ApiErrorBodySchema = z.object({
  error: z.object({ code: z.string(), message: z.string() }),
});

export const SourceSchema = z.enum(["paypal_sandbox", "demo_seed"]);
export type Source = z.infer<typeof SourceSchema>;

export function parseWith<T>(schema: z.ZodType<T>, data: unknown): T | null {
  const result = schema.safeParse(data);
  return result.success ? result.data : null;
}

const IsoDateTime = z.iso.datetime({ offset: true });

export const SyncRunSchema = z.object({
  id: z.string(),
  trigger: z.enum(["manual", "startup"]),
  period: z.object({ start: IsoDateTime, end: IsoDateTime }),
  started_at: IsoDateTime,
  finished_at: IsoDateTime.nullable(),
  outcome: z.enum(["running", "success", "partial", "failed"]),
  windows: z.object({ total: z.number().int(), done: z.number().int() }),
  counts: z.object({
    added: z.number().int(),
    updated: z.number().int(),
    skipped: z.number().int(),
    flagged: z.number().int(),
  }),
  error: z.object({ code: z.string(), message: z.string() }).nullable(),
  hint: z.string().nullable(),
});
export type SyncRun = z.infer<typeof SyncRunSchema>;
export const LastSyncSchema = SyncRunSchema.nullable();

export const RateSchema = z.string().regex(/^\d+\.\d{6}$/, "rate must be a 6-decimal string");
export const PercentSchema = z
  .string()
  .regex(/^-?\d+\.\d{2}$/, "percent must be a 2-decimal string");

export const LeakageSchema = z.object({
  mid_market_rate: RateSchema,
  paypal_rate: RateSchema,
  paypal_rate_simulated: z.literal(true),
  ideal_inr: MoneySchema,
  inr_received: MoneySchema,
  fee_loss_inr: MoneySchema,
  fx_loss_inr: MoneySchema,
  total_leakage_inr: MoneySchema,
  leakage_percent: PercentSchema.nullable(),
});
export type Leakage = z.infer<typeof LeakageSchema>;
export const LeakageStatusSchema = z.enum([
  "calculated",
  "rate_unavailable",
  "not_calculated",
  "not_applicable",
]);
export type LeakageStatus = z.infer<typeof LeakageStatusSchema>;

export const TransactionSchema = z.object({
  id: z.string(),
  paypal_transaction_id: z.string(),
  occurred_at: IsoDateTime,
  client: z.object({ id: z.string(), name: z.string(), country: z.string().nullable() }),
  kind: z.enum([
    "income",
    "outgoing_payment",
    "refund",
    "withdrawal",
    "conversion",
    "hold",
    "fee",
    "other",
  ]),
  status: z.enum(["completed", "pending", "denied", "reversed"]),
  gross: MoneySchema,
  fee: MoneySchema,
  net: MoneySchema,
  source: SourceSchema,
  is_flagged: z.boolean(),
  leakage_status: LeakageStatusSchema,
  leakage: LeakageSchema.nullable(),
});
export type Transaction = z.infer<typeof TransactionSchema>;

export const TransactionListSchema = z.object({
  items: z.array(TransactionSchema),
  total: z.number().int(),
  limit: z.number().int(),
  offset: z.number().int(),
});
export type TransactionList = z.infer<typeof TransactionListSchema>;

export const PayOrderOutSchema = z.object({ order_id: z.string() });

export const CaptureOutSchema = z.object({
  transaction_id: z.string(),
  order_id: z.string(),
  status: z.enum(["completed", "pending"]),
  gross: MoneySchema,
  recorded: z.boolean(),
});
export type CaptureOut = z.infer<typeof CaptureOutSchema>;
