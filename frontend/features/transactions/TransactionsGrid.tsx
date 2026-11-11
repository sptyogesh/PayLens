"use client";

import { DataGrid } from "@/components/ui/DataGrid";
import type { Transaction } from "@/lib/api/schemas";
import { TRANSACTIONS_TEXT } from "@/lib/constants";

import { TRANSACTION_COLUMNS } from "./columns";

/** Parent: the transactions table. Children in ./columns: payment and leakage columns. */
export function TransactionsGrid({ rows }: { rows: Transaction[] }) {
  return (
    <DataGrid<Transaction>
      rows={rows}
      columns={TRANSACTION_COLUMNS}
      label={TRANSACTIONS_TEXT.gridLabel}
      emptyTitle={TRANSACTIONS_TEXT.emptyTitle}
      emptyMessage={TRANSACTIONS_TEXT.emptyMessage}
      getRowId={(row) => row.id}
    />
  );
}
