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

const CENTS_PATTERN = /^(-?)(\d+)\.(\d{2})$/;

/** Exact comparison of 2-decimal money strings (for sorting), via integer cents. */
export function compareAmounts(a: string, b: string): number {
  const toCents = (value: string): bigint => {
    const match = CENTS_PATTERN.exec(value.trim());
    if (!match) return 0n;
    const cents = BigInt(`${match[2] ?? "0"}${match[3] ?? "00"}`);
    return match[1] === "-" ? -cents : cents;
  };
  const difference = toCents(a) - toCents(b);
  return difference === 0n ? 0 : difference > 0n ? 1 : -1;
}

/** Like compareAmounts, but rows without a value always sort last, in either direction. */
export function compareOptionalAmounts(
  a: string | null | undefined,
  b: string | null | undefined,
  isDescending = false,
): number {
  if (a == null || b == null) {
    if (a == b) return 0;
    const missingLast = a == null ? 1 : -1;
    return isDescending ? -missingLast : missingLast;
  }
  return compareAmounts(a, b);
}

/** "50" → "50.00", "5.5" → "5.50" (string padding only, no arithmetic). */
export function toTwoDecimals(amount: string): string {
  const [whole = "0", fraction = ""] = amount.trim().split(".");
  return `${whole}.${fraction.padEnd(2, "0").slice(0, 2)}`;
}

/** "7.25" → "7.25%" (display only; the percentage is computed by the backend). */
export function formatPercent(percent: string): string {
  return `${percent}%`;
}

/** A 6-decimal rate string shown as-is with the ₹ per unit context, e.g. "₹84.000000". */
export function formatRate(rate: string): string {
  return `₹${rate}`;
}
