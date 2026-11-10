import { Badge } from "@/components/ui/Badge";
import type { FiraStatus } from "@/lib/api/fira-schemas";
import { FIRA_STATUS_LABELS } from "@/lib/constants";

/** Matched / Needs review use the shared Badge; "No match" has no payment, so it is neutral. */
export function FiraStatusBadge({ status }: { status: FiraStatus }) {
  if (status !== "no_match") return <Badge variant={status} />;
  return (
    <span
      data-variant={status}
      className="inline-flex rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-800"
    >
      {FIRA_STATUS_LABELS.no_match}
    </span>
  );
}
