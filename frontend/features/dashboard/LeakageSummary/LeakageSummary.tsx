import { EmptyState } from "@/components/ui/EmptyState";
import type { Dashboard } from "@/lib/api/dashboard-schemas";
import { DASHBOARD_TEXT } from "@/lib/constants";

import { SummaryCards } from "./SummaryCards";
import { SummaryNotes } from "./SummaryNotes";

/** Child of DashboardView: cards (or an empty state) plus the notes that explain them. */
export function LeakageSummary({ data }: { data: Dashboard }) {
  return (
    <section className="space-y-4">
      {data.totals ? (
        <SummaryCards totals={data.totals} />
      ) : (
        <EmptyState title={DASHBOARD_TEXT.emptyTitle} message={DASHBOARD_TEXT.emptyMessage} />
      )}
      <SummaryNotes data={data} />
    </section>
  );
}
