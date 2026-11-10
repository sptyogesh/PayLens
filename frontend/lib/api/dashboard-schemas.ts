/** zod schemas for GET /dashboard (specs/002-leakage-dashboard/contracts/http-api.md). */
import { z } from "zod";

import { PERIOD_OPTIONS } from "../constants";

import { MoneySchema, PercentSchema, SourceSchema } from "./schemas";

const PERIOD_KEYS = PERIOD_OPTIONS.map((option) => option.value);
export const PeriodKeySchema = z.enum(PERIOD_KEYS as [PeriodValue, ...PeriodValue[]]);
type PeriodValue = (typeof PERIOD_OPTIONS)[number]["value"];
export type PeriodKey = z.infer<typeof PeriodKeySchema>;

export const TotalsSchema = z.object({
  payment_count: z.number().int(),
  income_inr: MoneySchema,
  fee_loss_inr: MoneySchema,
  fx_loss_inr: MoneySchema,
  total_leakage_inr: MoneySchema,
  leakage_percent: PercentSchema.nullable(),
});
export type Totals = z.infer<typeof TotalsSchema>;

export const BreakdownRowSchema = z.object({
  key: z.string(),
  label: z.string(),
  totals: TotalsSchema,
});
export type BreakdownRow = z.infer<typeof BreakdownRowSchema>;

const IsoDateTime = z.iso.datetime({ offset: true });

export const DashboardSchema = z.object({
  period: z.object({
    key: PeriodKeySchema,
    label: z.string(),
    start: IsoDateTime.nullable(),
    end: IsoDateTime.nullable(),
  }),
  totals: TotalsSchema.nullable(),
  excluded_count: z.number().int(),
  not_calculated_count: z.number().int(),
  sources: z.array(SourceSchema),
  paypal_rate_simulated: z.literal(true),
  simulated_spread_percent: PercentSchema,
  by_month: z.array(BreakdownRowSchema),
  by_client: z.array(BreakdownRowSchema),
});
export type Dashboard = z.infer<typeof DashboardSchema>;
