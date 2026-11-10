"use client";

import { useApi } from "@/hooks/useApi";
import { TransactionListSchema } from "@/lib/api/schemas";

export const TRANSACTIONS_PATH = "/transactions";

export function useTransactions() {
  return useApi(TRANSACTIONS_PATH, TransactionListSchema);
}
