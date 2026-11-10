"use client";

import type { ColDef } from "ag-grid-community";
import { AllCommunityModule, ModuleRegistry } from "ag-grid-community";
import { AgGridReact } from "ag-grid-react";

import { EmptyState } from "../EmptyState";

ModuleRegistry.registerModules([AllCommunityModule]);

const DEFAULT_COL_DEF: ColDef = { sortable: true, resizable: true, flex: 1, minWidth: 110 };
const GRID_HEIGHT_PX = 480;

export type DataGridProps<T> = {
  rows: T[];
  columns: ColDef<T>[];
  label: string;
  emptyTitle: string;
  emptyMessage?: string;
  getRowId?: (row: T) => string;
};

/** Every table in PayLens: AG Grid with shared defaults and an empty state. */
export function DataGrid<T>({
  rows,
  columns,
  label,
  emptyTitle,
  emptyMessage,
  getRowId,
}: DataGridProps<T>) {
  if (rows.length === 0) {
    return <EmptyState title={emptyTitle} {...(emptyMessage ? { message: emptyMessage } : {})} />;
  }
  return (
    <div role="region" aria-label={label} style={{ height: GRID_HEIGHT_PX }} className="w-full">
      <AgGridReact<T>
        rowData={rows}
        columnDefs={columns}
        defaultColDef={DEFAULT_COL_DEF as ColDef<T>}
        suppressRowVirtualisation
        suppressColumnVirtualisation
        {...(getRowId ? { getRowId: ({ data }: { data: T }) => getRowId(data) } : {})}
      />
    </div>
  );
}
