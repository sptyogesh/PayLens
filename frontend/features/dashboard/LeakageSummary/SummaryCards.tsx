import { MoneyText } from "@/components/ui/MoneyText";
import { StatCard } from "@/components/ui/StatCard";
import type { Totals } from "@/lib/api/dashboard-schemas";
import type { Money } from "@/lib/api/schemas";
import { DASHBOARD_TEXT } from "@/lib/constants";
import { formatPercent } from "@/lib/format";

const CARDS = DASHBOARD_TEXT.cards;

function MoneyValue({ value, gain = false }: { value: Money; gain?: boolean }) {
  return <MoneyText amount={value.amount} currency={value.currency} gainWhenNegative={gain} />;
}

/** The five summary cards (FR-030). Every value comes from the API; nothing is added here. */
export function SummaryCards({ totals }: { totals: Totals }) {
  const percent = totals.leakage_percent;
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
      <StatCard
        title={CARDS.income}
        value={<MoneyValue value={totals.income_inr} />}
        hint={DASHBOARD_TEXT.paymentsHint(totals.payment_count)}
      />
      <StatCard title={CARDS.feeLoss} value={<MoneyValue value={totals.fee_loss_inr} />} />
      <StatCard title={CARDS.fxLoss} value={<MoneyValue value={totals.fx_loss_inr} gain />} />
      <StatCard
        title={CARDS.totalLeakage}
        value={<MoneyValue value={totals.total_leakage_inr} />}
        hint={DASHBOARD_TEXT.simulatedHint}
      />
      <StatCard
        title={CARDS.leakagePercent}
        value={percent ? formatPercent(percent) : DASHBOARD_TEXT.noPercent}
        hint={DASHBOARD_TEXT.simulatedHint}
      />
    </div>
  );
}
