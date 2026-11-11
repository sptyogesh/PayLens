"use client";

import { useApi } from "@/hooks/useApi";
import { TransactionListSchema } from "@/lib/api/schemas";
import { TRANSACTIONS_PAGE_MAX } from "@/lib/constants";

export const TRANSACTIONS_PATH = "/transactions";

/** The newest TRANSACTIONS_PAGE_MAX payments; `total` says how many exist in all. */
export function useTransactions() {
  return useApi(
    `${TRANSACTIONS_PATH}?limit=${String(TRANSACTIONS_PAGE_MAX)}`,
    TransactionListSchema,
  );
}
