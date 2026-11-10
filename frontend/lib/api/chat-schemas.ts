/** zod schemas for POST /chat (specs/003-ask-your-money/contracts/http-api.md). */
import { z } from "zod";

import { MoneySchema, PercentSchema } from "./schemas";

const CountSchema = z.string().regex(/^\d+$/, "count must be a whole-number string");

/** Money and percent values stay strings; their format is checked, never converted. */
function hasValidValue(figure: { kind: string; value: string; currency: string | null }) {
  if (figure.kind === "money") {
    const amount = MoneySchema.shape.amount.safeParse(figure.value).success;
    const currency = MoneySchema.shape.currency.safeParse(figure.currency).success;
    return amount && currency;
  }
  if (figure.kind === "percent") return PercentSchema.safeParse(figure.value).success;
  return CountSchema.safeParse(figure.value).success;
}

export const FigureSchema = z
  .object({
    label: z.string(),
    kind: z.enum(["money", "count", "percent"]),
    value: z.string(),
    currency: z.string().nullable(),
    period: z.string(),
  })
  .refine(hasValidValue, { message: "figure value does not match its kind" });
export type Figure = z.infer<typeof FigureSchema>;

export const ChatOutcomeSchema = z.enum(["answered", "no_data", "fallback"]);
export type ChatOutcome = z.infer<typeof ChatOutcomeSchema>;

export const ChatOutSchema = z.object({
  answer: z.string(),
  outcome: ChatOutcomeSchema,
  periods: z.array(z.string()),
  figures: z.array(FigureSchema),
  disclaimer: z.string().nullable(),
  tools_used: z.array(z.string()),
});
export type ChatOut = z.infer<typeof ChatOutSchema>;

export type ChatTurn = { role: "user" | "assistant"; content: string };
export type ChatIn = { question: string; history: ChatTurn[] };
