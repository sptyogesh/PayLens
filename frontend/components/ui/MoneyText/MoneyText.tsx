import { GAIN_LABEL } from "@/lib/constants";
import { absoluteAmount, formatMoney, isNegativeAmount } from "@/lib/format";

export type MoneyTextProps = {
  amount: string;
  currency: string;
  /** For losses (e.g. FX loss): a negative value is a gain and is shown as one. */
  gainWhenNegative?: boolean;
  className?: string;
};

/** Every money value on screen goes through this component. */
export function MoneyText({
  amount,
  currency,
  gainWhenNegative = false,
  className = "",
}: MoneyTextProps) {
  if (gainWhenNegative && isNegativeAmount(amount)) {
    return (
      <span className={`text-green-800 tabular-nums ${className}`}>
        {formatMoney(absoluteAmount(amount), currency)}{" "}
        <span className="text-xs">({GAIN_LABEL})</span>
      </span>
    );
  }
  return <span className={`tabular-nums ${className}`}>{formatMoney(amount, currency)}</span>;
}
