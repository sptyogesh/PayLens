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
});
export type Transaction = z.infer<typeof TransactionSchema>;

export const TransactionListSchema = z.object({
  items: z.array(TransactionSchema),
  total: z.number().int(),
  limit: z.number().int(),
  offset: z.number().int(),
});
export type TransactionList = z.infer<typeof TransactionListSchema>;
