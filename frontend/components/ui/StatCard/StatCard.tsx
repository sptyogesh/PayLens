import type { ReactNode } from "react";
import { useId } from "react";

import { Card } from "../Card";

export type StatCardProps = {
  title: string;
  /** The main figure; pass a `MoneyText` for money values. */
  value: ReactNode;
  hint?: ReactNode;
};

/** A dashboard summary card: small title, large value, optional hint. */
export function StatCard({ title, value, hint }: StatCardProps) {
  const titleId = useId();
  return (
    <Card>
      <div role="group" aria-labelledby={titleId}>
        <p id={titleId} className="text-sm font-medium text-slate-600">
          {title}
        </p>
        <p className="mt-1 text-2xl font-semibold text-slate-900">{value}</p>
        {hint ? <p className="mt-1 text-xs text-slate-600">{hint}</p> : null}
      </div>
    </Card>
  );
}
