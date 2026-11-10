"use client";

import type { ColDef, ICellRendererParams } from "ag-grid-community";

import { Badge } from "@/components/ui/Badge";
import { DataGrid } from "@/components/ui/DataGrid";
import { MoneyText } from "@/components/ui/MoneyText";
import type { Money, Transaction } from "@/lib/api/schemas";
import { TRANSACTION_STATUS_LABELS, TRANSACTIONS_TEXT } from "@/lib/constants";
import { compareAmounts, formatDate } from "@/lib/format";

type Cell = ICellRendererParams<Transaction>;
type MoneyField = "gross" | "fee" | "net";

function moneyColumn(field: MoneyField, headerName: string): ColDef<Transaction> {
  return {
    colId: field,
    headerName,
    valueGetter: ({ data }) => data?.[field],
    comparator: (a: Money, b: Money) => compareAmounts(a.amount, b.amount),
    cellRenderer: ({ value }: ICellRendererParams<Transaction, Money>) =>
      value ? <MoneyText amount={value.amount} currency={value.currency} /> : null,
  };
}

const COLUMNS: ColDef<Transaction>[] = [
  {
    colId: "date",
    headerName: "Date (IST)",
    field: "occurred_at",
    sort: "desc",
    valueFormatter: ({ value }: { value: string }) => formatDate(value),
  },
  { colId: "client", headerName: "Client", valueGetter: ({ data }) => data?.client.name },
  moneyColumn("gross", "Gross"),
  moneyColumn("fee", "PayPal fee"),
  moneyColumn("net", "Net"),
  {
    colId: "status",
    headerName: "Status",
    valueGetter: ({ data }) => (data ? TRANSACTION_STATUS_LABELS[data.status] : ""),
  },
  {
    colId: "source",
    headerName: "Source",
    field: "source",
    cellRenderer: ({ data }: Cell) =>
      data ? (
        <>
          <Badge variant={data.source} />
          {data.is_flagged ? (
            <span title={TRANSACTIONS_TEXT.flaggedHint} className="ml-2 text-xs text-orange-800">
              {TRANSACTIONS_TEXT.flagged}
            </span>
          ) : null}
        </>
      ) : null,
  },
];

export function TransactionsGrid({ rows }: { rows: Transaction[] }) {
  return (
    <DataGrid<Transaction>
      rows={rows}
      columns={COLUMNS}
      label={TRANSACTIONS_TEXT.gridLabel}
      emptyTitle={TRANSACTIONS_TEXT.emptyTitle}
      emptyMessage={TRANSACTIONS_TEXT.emptyMessage}
      getRowId={(row) => row.id}
    />
  );
}
