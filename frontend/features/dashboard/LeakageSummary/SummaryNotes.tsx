import { Disclaimer } from "@/components/ui/Disclaimer";
import type { Dashboard } from "@/lib/api/dashboard-schemas";
import { DASHBOARD_TEXT, SOURCE_LABELS } from "@/lib/constants";

/** Period, data sources, excluded payments and the simulated-rate notice (FR-033, FR-036). */
export function SummaryNotes({ data }: { data: Dashboard }) {
  const sources = data.sources.map((source) => SOURCE_LABELS[source]).join(", ");
  return (
    <div className="space-y-2 text-sm text-slate-700">
      <p>
        {DASHBOARD_TEXT.showing}: <strong>{data.period.label}</strong>
        {sources ? ` · ${DASHBOARD_TEXT.includes}: ${sources}` : null}
      </p>
      {data.excluded_count > 0 ? (
        <p role="note" className="text-amber-900">
          {DASHBOARD_TEXT.excluded(data.excluded_count)}
        </p>
      ) : null}
      {data.not_calculated_count > 0 ? (
        <p role="note" className="text-amber-900">
          {DASHBOARD_TEXT.notCalculated(data.not_calculated_count)}
        </p>
      ) : null}
      <Disclaimer text={DASHBOARD_TEXT.spreadNote(data.simulated_spread_percent)} />
    </div>
  );
}
