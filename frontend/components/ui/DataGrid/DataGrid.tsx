"use client";

import type { ColDef, GetRowIdParams } from "ag-grid-community";
import { AllCommunityModule, ModuleRegistry } from "ag-grid-community";
import { AgGridReact } from "ag-grid-react";
import { useCallback, useEffect, useRef } from "react";

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
  /** Grow with the rows instead of a fixed-height scroll area (small tables). */
  autoHeight?: boolean;
};

/** Every table in PayLens: AG Grid with shared defaults and an empty state. */
export function DataGrid<T>({
  rows,
  columns,
  label,
  emptyTitle,
  emptyMessage,
  getRowId,
  autoHeight = false,
}: DataGridProps<T>) {
  const stableGetRowId = useStableGetRowId(getRowId);
  if (rows.length === 0) {
    return <EmptyState title={emptyTitle} {...(emptyMessage ? { message: emptyMessage } : {})} />;
  }
  return (
    <div
      role="region"
      aria-label={label}
      style={autoHeight ? undefined : { height: GRID_HEIGHT_PX }}
      className="w-full"
    >
      <AgGridReact<T>
        rowData={rows}
        columnDefs={columns}
        defaultColDef={DEFAULT_COL_DEF as ColDef<T>}
        suppressRowVirtualisation
        {...(autoHeight ? { domLayout: "autoHeight" as const } : {})}
        suppressColumnVirtualisation
        {...(getRowId ? { getRowId: stableGetRowId } : {})}
      />
    </div>
  );
}

/**
 * getRowId is an initial-only AG Grid property: a new function on every render makes AG Grid
 * warn. Keep one function for the grid's life that always calls the latest `getRowId`.
 */
function useStableGetRowId<T>(getRowId: ((row: T) => string) | undefined) {
  const latest = useRef(getRowId);
  useEffect(() => {
    latest.current = getRowId;
  }, [getRowId]);
  return useCallback(({ data }: GetRowIdParams<T>) => latest.current?.(data) ?? "", []);
}
