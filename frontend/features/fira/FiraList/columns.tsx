import type { ColDef, ICellRendererParams } from "ag-grid-community";

import { MoneyText } from "@/components/ui/MoneyText";
import type { FiraItem } from "@/lib/api/fira-schemas";
import type { Money } from "@/lib/api/schemas";
import { FIRA_REASON_MIN_WIDTH_PX, FIRA_STATUS_LABELS, FIRA_TEXT } from "@/lib/constants";
import { formatDay } from "@/lib/format";

import { FiraStatusBadge } from "../FiraStatusBadge";

const COLS = FIRA_TEXT.columns;
const orDash = (value: string | number | null) => (value === null ? FIRA_TEXT.none : value);

function moneyColumn(key: "foreign_amount" | "inr_amount", headerName: string): ColDef<FiraItem> {
  return {
    colId: key,
    headerName,
    sortable: false,
    cellRenderer: ({ data }: ICellRendererParams<FiraItem>) => {
      const money: Money | null | undefined = data?.[key];
      return money ? <MoneyText amount={money.amount} currency={money.currency} /> : FIRA_TEXT.none;
    },
  };
}

/** FIRA list columns: extracted fields, status, score, reason and linked payments. */
export const FIRA_COLUMNS: ColDef<FiraItem>[] = [
  { colId: "file", headerName: COLS.file, field: "file_name" },
  {
    colId: "reference",
    headerName: COLS.reference,
    valueGetter: ({ data }) => orDash(data?.reference_no ?? null),
  },
  {
    colId: "date",
    headerName: COLS.date,
    valueGetter: ({ data }) => data?.remittance_date ?? null,
    valueFormatter: ({ value }: { value: string | null }) =>
      value ? formatDay(value) : FIRA_TEXT.none,
  },
  moneyColumn("foreign_amount", COLS.foreign),
  moneyColumn("inr_amount", COLS.inr),
  {
    colId: "status",
    headerName: COLS.status,
    valueGetter: ({ data }) => (data ? FIRA_STATUS_LABELS[data.status] : ""),
    cellRenderer: ({ data }: ICellRendererParams<FiraItem>) =>
      data ? <FiraStatusBadge status={data.status} /> : null,
  },
  {
    colId: "score",
    headerName: COLS.score,
    valueGetter: ({ data }) => data?.score ?? null,
    valueFormatter: ({ value }: { value: number | null }) => String(orDash(value)),
  },
  {
    colId: "reason",
    headerName: COLS.reason,
    valueGetter: ({ data }) => orDash(data?.reason ?? null),
    minWidth: FIRA_REASON_MIN_WIDTH_PX,
  },
  {
    colId: "payments",
    headerName: COLS.payments,
    sortable: false,
    valueGetter: ({ data }) =>
      data && data.matches.length > 0
        ? data.matches.map((match) => match.paypal_transaction_id).join(", ")
        : FIRA_TEXT.none,
  },
];
