"use client";

import type { ColDef, ICellRendererParams } from "ag-grid-community";

import { DataGrid } from "@/components/ui/DataGrid";
import { MoneyText } from "@/components/ui/MoneyText";
import type { MissingPayment } from "@/lib/api/fira-schemas";
import { FIRA_TEXT } from "@/lib/constants";
import { formatDay } from "@/lib/format";

const COLS = FIRA_TEXT.columns;

const COLUMNS: ColDef<MissingPayment>[] = [
  {
    colId: "date",
    headerName: COLS.paymentDate,
    field: "date",
    sort: "desc",
    valueFormatter: ({ value }: { value: string }) => formatDay(value),
  },
  { colId: "client", headerName: COLS.client, field: "client" },
  { colId: "paypal_transaction_id", headerName: COLS.paymentId, field: "paypal_transaction_id" },
  {
    colId: "gross",
    headerName: COLS.gross,
    sortable: false,
    cellRenderer: ({ data }: ICellRendererParams<MissingPayment>) =>
      data ? <MoneyText amount={data.gross.amount} currency={data.gross.currency} /> : null,
  },
];

/** Child of FiraView: completed income payments that have no FIRA yet. */
export function MissingList({ rows }: { rows: MissingPayment[] }) {
  return (
    <DataGrid<MissingPayment>
      rows={rows}
      columns={COLUMNS}
      label={FIRA_TEXT.missingLabel}
      emptyTitle={FIRA_TEXT.missingEmptyTitle}
      getRowId={(row) => row.transaction_id}
      autoHeight
    />
  );
}
