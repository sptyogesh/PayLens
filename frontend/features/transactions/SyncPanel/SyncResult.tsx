import { ErrorState } from "@/components/ui/ErrorState";
import type { ApiError } from "@/lib/api/client";
import type { SyncRun } from "@/lib/api/schemas";
import { SYNC_TEXT } from "@/lib/constants";
import { formatDate } from "@/lib/format";

export type SyncResultProps = { run: SyncRun | null; error: ApiError | null };

/** Grandchild of SyncPanel: the last sync summary, its error, and request errors (409/429). */
export function SyncResult({ run, error }: SyncResultProps) {
  return (
    <div aria-live="polite" className="space-y-2 text-sm">
      {error ? <ErrorState message={error.message} /> : null}
      {run ? <RunSummary run={run} /> : <p className="text-slate-600">{SYNC_TEXT.neverRun}</p>}
    </div>
  );
}

function RunSummary({ run }: { run: SyncRun }) {
  const { added, updated, skipped, flagged } = run.counts;
  return (
    <div className="space-y-1">
      <p className="font-medium">
        {SYNC_TEXT.outcome[run.outcome]} ({SYNC_TEXT.trigger[run.trigger]})
        {run.finished_at ? ` · ${formatDate(run.finished_at)}` : ""}
      </p>
      <p>
        Added {added} · Updated {updated} · Skipped {skipped} · Flagged {flagged}
      </p>
      <p className="text-slate-600">
        Period: {formatDate(run.period.start)} – {formatDate(run.period.end)}
      </p>
      {run.error ? <ErrorState message={run.error.message} /> : null}
      {run.hint ? <p className="text-slate-600">{run.hint}</p> : null}
    </div>
  );
}
