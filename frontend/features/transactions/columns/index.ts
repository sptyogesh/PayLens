import type { ColDef } from "ag-grid-community";

import type { Transaction } from "@/lib/api/schemas";

import { BASE_COLUMNS } from "./baseColumns";
import { FIRA_COLUMN } from "./firaColumn";
import { LEAKAGE_COLUMNS } from "./leakageColumns";

export const TRANSACTION_COLUMNS: ColDef<Transaction>[] = [
  ...BASE_COLUMNS,
  FIRA_COLUMN,
  ...LEAKAGE_COLUMNS,
];
