import type { ColDef, ICellRendererParams } from "ag-grid-community";

import { MoneyText } from "@/components/ui/MoneyText";
import type { BreakdownRow, Totals } from "@/lib/api/dashboard-schemas";
import { DASHBOARD_TEXT, LEAKAGE_TEXT } from "@/lib/constants";
import { compareAmounts, formatPercent } from "@/lib/format";

type MoneyKey = "income_inr" | "fee_loss_inr" | "fx_loss_inr" | "total_leakage_inr";

function moneyColumn(key: MoneyKey, headerName: string, gain = false): ColDef<BreakdownRow> {
  return {
    colId: key,
    headerName,
    valueGetter: ({ data }) => data?.totals[key].amount,
    comparator: compareAmounts,
    cellRenderer: ({ data }: ICellRendererParams<BreakdownRow>) => {
      const money = data?.totals[key];
      return money ? (
        <MoneyText amount={money.amount} currency={money.currency} gainWhenNegative={gain} />
      ) : null;
    },
  };
}

const percent = (totals: Totals | undefined) =>
  totals?.leakage_percent ? formatPercent(totals.leakage_percent) : DASHBOARD_TEXT.noPercent;

/** Columns shared by the month and client tables; `labelHeader` names the first column. */
export function breakdownColumns(labelHeader: string): ColDef<BreakdownRow>[] {
  return [
    {
      colId: "label",
      headerName: labelHeader,
      field: "label",
      sortable: false,
      minWidth: DASHBOARD_TEXT.labelColumnMinWidthPx,
    },
    {
      colId: "payments",
      headerName: DASHBOARD_TEXT.columns.payments,
      valueGetter: ({ data }) => data?.totals.payment_count,
    },
    moneyColumn("income_inr", DASHBOARD_TEXT.columns.income),
    moneyColumn("fee_loss_inr", LEAKAGE_TEXT.feeLoss),
    moneyColumn("fx_loss_inr", LEAKAGE_TEXT.fxLoss, true),
    moneyColumn("total_leakage_inr", LEAKAGE_TEXT.totalLeakage),
    {
      colId: "leakage_percent",
      headerName: LEAKAGE_TEXT.leakagePercent,
      valueGetter: ({ data }) => percent(data?.totals),
      sortable: false,
    },
  ];
}
