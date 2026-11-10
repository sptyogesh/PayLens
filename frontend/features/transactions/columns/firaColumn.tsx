import type { ColDef, ICellRendererParams } from "ag-grid-community";

import { Badge } from "@/components/ui/Badge";
import type { Transaction } from "@/lib/api/schemas";
import { FIRA_LABELS, FIRA_TEXT } from "@/lib/constants";

/** FIRA badge per payment (specs/004-fira-matching FR-009); "—" when the row has none. */
export const FIRA_COLUMN: ColDef<Transaction> = {
  colId: "fira",
  headerName: FIRA_TEXT.column,
  valueGetter: ({ data }) => (data?.fira_status ? FIRA_LABELS[data.fira_status] : null),
  cellRenderer: ({ data }: ICellRendererParams<Transaction>) =>
    data?.fira_status ? <Badge variant={data.fira_status} /> : FIRA_TEXT.none,
};
