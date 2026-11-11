import type { ColDef, ICellRendererParams } from "ag-grid-community";

import { MoneyText } from "@/components/ui/MoneyText";
import type { Leakage, Transaction } from "@/lib/api/schemas";
import { LEAKAGE_TEXT } from "@/lib/constants";
import { compareOptionalAmounts, formatPercent, formatRate } from "@/lib/format";

/** Exact sort; rows without leakage stay last whichever way the column is sorted. */
const sortMissingLast: NonNullable<ColDef<Transaction>["comparator"]> = (
  a,
  b,
  _nodeA,
  _nodeB,
  desc,
) => compareOptionalAmounts(a as string | null, b as string | null, desc);

type MoneyKey = "inr_received" | "fee_loss_inr" | "fx_loss_inr" | "total_leakage_inr";
type TextKey = "mid_market_rate" | "paypal_rate" | "leakage_percent";

/** "Rate unavailable" / "Not calculated" instead of numbers (Principle III). */
function StatusText({ data }: { data: Transaction }) {
  const status = data.leakage_status;
  if (status === "calculated") return null;
  return (
    <span title={LEAKAGE_TEXT.statusHint[status]} className="text-xs text-slate-600">
      {LEAKAGE_TEXT.status[status]}
    </span>
  );
}

function moneyColumn(key: MoneyKey, headerName: string, gain = false): ColDef<Transaction> {
  return {
    colId: key,
    headerName,
    valueGetter: ({ data }) => data?.leakage?.[key].amount ?? null,
    comparator: sortMissingLast,
    cellRenderer: ({ data }: ICellRendererParams<Transaction>) => {
      if (!data) return null;
      const money = data.leakage?.[key];
      if (!money) return <StatusText data={data} />;
      return <MoneyText amount={money.amount} currency={money.currency} gainWhenNegative={gain} />;
    },
  };
}

function textColumn(
  key: TextKey,
  headerName: string,
  format: (value: string) => string,
): ColDef<Transaction> {
  return {
    colId: key,
    headerName,
    valueGetter: ({ data }) => (data?.leakage ? data.leakage[key] : null),
    ...(key === "leakage_percent" ? { comparator: sortMissingLast } : { sortable: false }),
    cellRenderer: ({ data, value }: ICellRendererParams<Transaction, Leakage[TextKey]>) => {
      if (!data) return null;
      return value ? (
        <span className="tabular-nums">{format(value)}</span>
      ) : (
        <StatusText data={data} />
      );
    },
  };
}

/** Leakage in INR (Phase 1A plan section 10); simulated values carry the label (FR-004). */
export const LEAKAGE_COLUMNS: ColDef<Transaction>[] = [
  textColumn("mid_market_rate", LEAKAGE_TEXT.midRate, formatRate),
  textColumn("paypal_rate", LEAKAGE_TEXT.paypalRate, formatRate),
  moneyColumn("inr_received", LEAKAGE_TEXT.inrReceived),
  moneyColumn("fee_loss_inr", LEAKAGE_TEXT.feeLoss),
  moneyColumn("fx_loss_inr", LEAKAGE_TEXT.fxLoss, true),
  moneyColumn("total_leakage_inr", LEAKAGE_TEXT.totalLeakage),
  textColumn("leakage_percent", LEAKAGE_TEXT.leakagePercent, formatPercent),
];
