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
