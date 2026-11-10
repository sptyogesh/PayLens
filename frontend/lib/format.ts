/**
 * Display formatting only. Money stays a decimal string end to end; the frontend never does
 * money arithmetic (constitution Principle IV). Intl formats the string without a float.
 */
import { DISPLAY_LOCALE, DISPLAY_TIME_ZONE } from "./constants";

export function formatMoney(amount: string, currency: string): string {
  const formatter = new Intl.NumberFormat(DISPLAY_LOCALE, {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  return formatter.format(amount as Intl.StringNumericLiteral);
}

export function formatINR(amount: string): string {
  return formatMoney(amount, "INR");
}

export function isNegativeAmount(amount: string): boolean {
  return amount.trim().startsWith("-");
}

export function absoluteAmount(amount: string): string {
  const trimmed = amount.trim();
  return trimmed.startsWith("-") ? trimmed.slice(1) : trimmed;
}

/** ISO 8601 UTC → date and time in IST. */
export function formatDate(iso: string): string {
  return new Intl.DateTimeFormat(DISPLAY_LOCALE, {
    timeZone: DISPLAY_TIME_ZONE,
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(iso));
}
