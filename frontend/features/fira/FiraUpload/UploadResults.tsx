import type { FiraOutcome, FiraUploadResult } from "@/lib/api/fira-schemas";
import { FIRA_OUTCOME_LABELS, FIRA_TEXT } from "@/lib/constants";

import { FiraStatusBadge } from "../FiraStatusBadge";

const OUTCOME_CLASSES: Record<FiraOutcome, string> = {
  stored: "bg-green-100 text-green-900",
  duplicate: "bg-amber-100 text-amber-900",
  rejected: "bg-red-100 text-red-900",
  failed: "bg-red-100 text-red-900",
};

/** Grandchild of FiraView: one line per uploaded file with its outcome and the server message. */
export function UploadResults({ results }: { results: FiraUploadResult[] }) {
  if (results.length === 0) return null;
  return (
    <ul aria-label={FIRA_TEXT.resultsLabel} className="divide-y divide-slate-200 text-sm">
      {results.map((result, index) => (
        <li key={`${result.file_name}-${String(index)}`} className="space-y-1 py-2">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-medium break-all text-slate-900">{result.file_name}</span>
            <span
              className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${OUTCOME_CLASSES[result.outcome]}`}
            >
              {FIRA_OUTCOME_LABELS[result.outcome]}
            </span>
            {result.status ? <FiraStatusBadge status={result.status} /> : null}
          </div>
          <p className="text-slate-700">{result.message}</p>
        </li>
      ))}
    </ul>
  );
}
