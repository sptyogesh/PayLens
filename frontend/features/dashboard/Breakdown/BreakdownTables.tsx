import { DataGrid } from "@/components/ui/DataGrid";
import type { BreakdownRow, Dashboard } from "@/lib/api/dashboard-schemas";
import { DASHBOARD_TEXT } from "@/lib/constants";

import { breakdownColumns } from "./breakdownColumns";

const MONTH_COLUMNS = breakdownColumns(DASHBOARD_TEXT.columns.month);
const CLIENT_COLUMNS = breakdownColumns(DASHBOARD_TEXT.columns.client);

function Table({
  title,
  rows,
  columns,
}: {
  title: string;
  rows: BreakdownRow[];
  columns: typeof MONTH_COLUMNS;
}) {
  return (
    <section className="space-y-2">
      <h2 className="text-lg font-semibold">{title}</h2>
      <DataGrid<BreakdownRow>
        rows={rows}
        columns={columns}
        label={title}
        emptyTitle={DASHBOARD_TEXT.emptyTitle}
        getRowId={(row) => row.key}
        autoHeight
      />
    </section>
  );
}

/** Child of DashboardView (FR-032): where the leakage comes from, by month and by client. */
export function BreakdownTables({ data }: { data: Dashboard }) {
  if (!data.totals) return null;
  return (
    <div className="space-y-6">
      <Table title={DASHBOARD_TEXT.byMonth} rows={data.by_month} columns={MONTH_COLUMNS} />
      <Table title={DASHBOARD_TEXT.byClient} rows={data.by_client} columns={CLIENT_COLUMNS} />
    </div>
  );
}
