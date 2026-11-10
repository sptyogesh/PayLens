"use client";

/**
 * Parent for the transactions page. Children: SyncPanel (Sync now + result) and
 * TransactionsGrid (the list). Data comes from useTransactions and useSync.
 */
import { PageHeader } from "@/components/layout/PageHeader";
import { ErrorState } from "@/components/ui/ErrorState";
import { Spinner } from "@/components/ui/Spinner";
import { TRANSACTIONS_TEXT } from "@/lib/constants";

import { SyncPanel } from "./SyncPanel";
import { TransactionsGrid } from "./TransactionsGrid";
import { useSync } from "./useSync";
import { useTransactions } from "./useTransactions";

export function TransactionsView() {
  const transactions = useTransactions();
  const sync = useSync(transactions.reload);
  return (
    <>
      <PageHeader title={TRANSACTIONS_TEXT.title} />
      <div className="space-y-6">
        <SyncPanel sync={sync} />
        {transactions.status === "loading" ? <Spinner /> : null}
        {transactions.status === "error" ? (
          <ErrorState message={transactions.error.message} onRetry={transactions.reload} />
        ) : null}
        {transactions.status === "success" ? (
          <TransactionsGrid rows={transactions.data.items} />
        ) : null}
      </div>
    </>
  );
}
