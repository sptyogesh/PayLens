import type { ReactNode } from "react";

import { DISCLAIMERS } from "@/lib/constants";

export type PageHeaderProps = { title: string; actions?: ReactNode };

/** Page title plus the demo-mode banner shown on every page (FR-050). */
export function PageHeader({ title, actions }: PageHeaderProps) {
  return (
    <div className="mb-6 space-y-3">
      <p
        role="note"
        className="rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900"
      >
        {DISCLAIMERS.demoMode}
      </p>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold">{title}</h1>
        {actions}
      </div>
    </div>
  );
}
