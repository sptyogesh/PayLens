/** Checkout form validation; mirrors backend PayOrderIn (FR-031). */
import { z } from "zod";

import {
  CHECKOUT_CURRENCIES,
  CHECKOUT_DESCRIPTION_MAX,
  CHECKOUT_MAX_AMOUNT,
  PAY_TEXT,
} from "@/lib/constants";
import { compareAmounts, toTwoDecimals } from "@/lib/format";

const AMOUNT_PATTERN = /^\d+(\.\d{1,2})?$/;

export const PayFormSchema = z.object({
  amount: z
    .string()
    .trim()
    .regex(AMOUNT_PATTERN, PAY_TEXT.errors.amountFormat)
    .refine((v) => compareAmounts(toTwoDecimals(v), "0.00") > 0, PAY_TEXT.errors.amountMin)
    .refine(
      (v) => compareAmounts(toTwoDecimals(v), CHECKOUT_MAX_AMOUNT) <= 0,
      PAY_TEXT.errors.amountMax,
    ),
  currency: z.enum(CHECKOUT_CURRENCIES),
  description: z.string().max(CHECKOUT_DESCRIPTION_MAX, PAY_TEXT.errors.description),
});

export type PayFormValues = z.input<typeof PayFormSchema>;
export type PayFormErrors = Partial<Record<keyof PayFormValues, string>>;

export const EMPTY_FORM: PayFormValues = { amount: "", currency: "USD", description: "" };

export function validatePayForm(values: PayFormValues): {
  order: PayFormValues | null;
  errors: PayFormErrors;
} {
  const result = PayFormSchema.safeParse(values);
  if (result.success) return { order: result.data, errors: {} };
  const errors: PayFormErrors = {};
  for (const issue of result.error.issues) {
    const field = issue.path[0] as keyof PayFormValues;
    errors[field] ??= issue.message;
  }
  return { order: null, errors };
}

/** The API body: amount normalised to 2 decimals, blank description omitted. */
export function toOrderBody(order: PayFormValues) {
  const description = order.description.trim();
  return {
    amount: toTwoDecimals(order.amount),
    currency: order.currency,
    ...(description ? { description } : {}),
  };
}
