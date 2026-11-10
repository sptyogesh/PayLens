"use client";

import { DataGrid } from "@/components/ui/DataGrid";
import type { FiraItem } from "@/lib/api/fira-schemas";
import { FIRA_TEXT } from "@/lib/constants";

import { FIRA_COLUMNS } from "./columns";

/** Child of FiraView: every uploaded FIRA with its status. Columns live in ./columns. */
export function FiraList({ rows }: { rows: FiraItem[] }) {
  return (
    <DataGrid<FiraItem>
      rows={rows}
      columns={FIRA_COLUMNS}
      label={FIRA_TEXT.listLabel}
      emptyTitle={FIRA_TEXT.listEmptyTitle}
      emptyMessage={FIRA_TEXT.listEmptyMessage}
      getRowId={(row) => row.id}
    />
  );
}
