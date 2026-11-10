import { StatCard } from "@/components/ui/StatCard";
import type { FiraSummary as Summary } from "@/lib/api/fira-schemas";
import { FIRA_TEXT } from "@/lib/constants";

const CARDS = FIRA_TEXT.cards;

/** Child of FiraView: the four counts, exactly as the API returns them. */
export function FiraSummary({ summary }: { summary: Summary }) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <StatCard title={CARDS.matched} value={summary.matched} />
      <StatCard title={CARDS.needsReview} value={summary.needs_review} />
      <StatCard title={CARDS.noMatch} value={summary.no_match} />
      <StatCard title={CARDS.missing} value={summary.missing_payments} />
    </div>
  );
}
