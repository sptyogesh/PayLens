import { SegmentedControl } from "@/components/ui/SegmentedControl";
import type { PeriodKey } from "@/lib/api/dashboard-schemas";
import { DASHBOARD_TEXT, PERIOD_OPTIONS } from "@/lib/constants";

export type PeriodFilterProps = { value: PeriodKey; onChange: (period: PeriodKey) => void };

export function PeriodFilter({ value, onChange }: PeriodFilterProps) {
  return (
    <SegmentedControl<PeriodKey>
      label={DASHBOARD_TEXT.periodLabel}
      options={PERIOD_OPTIONS}
      value={value}
      onChange={onChange}
    />
  );
}
