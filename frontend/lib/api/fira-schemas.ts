/** zod schemas for POST /fira/upload and GET /fira (specs/004-fira-matching/contracts). */
import { z } from "zod";

import { IsoDateTime, MoneySchema, RateSchema } from "./schemas";

const Count = z.number().int().nonnegative();
const Score = z.number().int();
const IsoDate = z.iso.date();

export const FiraStatusSchema = z.enum(["matched", "needs_review", "no_match"]);
export type FiraStatus = z.infer<typeof FiraStatusSchema>;

export const FiraOutcomeSchema = z.enum(["stored", "duplicate", "rejected", "failed"]);
export type FiraOutcome = z.infer<typeof FiraOutcomeSchema>;

export const FiraSummarySchema = z.object({
  matched: Count,
  needs_review: Count,
  no_match: Count,
  missing_payments: Count,
});
export type FiraSummary = z.infer<typeof FiraSummarySchema>;

export const FiraUploadResultSchema = z.object({
  file_name: z.string(),
  outcome: FiraOutcomeSchema,
  message: z.string(),
  fira_id: z.string().nullable(),
  status: FiraStatusSchema.nullable(),
});
export type FiraUploadResult = z.infer<typeof FiraUploadResultSchema>;

export const FiraUploadOutSchema = z.object({
  result: FiraUploadResultSchema,
  summary: FiraSummarySchema,
});
export type FiraUploadOut = z.infer<typeof FiraUploadOutSchema>;

export const FiraMatchSchema = z.object({
  transaction_id: z.string(),
  paypal_transaction_id: z.string(),
  score: Score,
  kind: z.enum(["direct", "weekly"]),
});

export const FiraItemSchema = z.object({
  id: z.string(),
  file_name: z.string(),
  status: FiraStatusSchema,
  score: Score.nullable(),
  reason: z.string().nullable(),
  foreign_amount: MoneySchema.nullable(),
  inr_amount: MoneySchema.nullable(),
  rate: RateSchema.nullable(),
  remittance_date: IsoDate.nullable(),
  reference_no: z.string().nullable(),
  remitter: z.string().nullable(),
  purpose_code: z.string().nullable(),
  uploaded_at: IsoDateTime,
  matches: z.array(FiraMatchSchema),
});
export type FiraItem = z.infer<typeof FiraItemSchema>;

export const MissingPaymentSchema = z.object({
  transaction_id: z.string(),
  paypal_transaction_id: z.string(),
  /** The payment's IST calendar date. */
  date: IsoDate,
  client: z.string(),
  gross: MoneySchema,
});
export type MissingPayment = z.infer<typeof MissingPaymentSchema>;

export const FiraListSchema = z.object({
  summary: FiraSummarySchema,
  items: z.array(FiraItemSchema),
  missing: z.array(MissingPaymentSchema),
});
export type FiraList = z.infer<typeof FiraListSchema>;
