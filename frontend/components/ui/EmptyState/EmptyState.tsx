import type { ReactNode } from "react";

export type EmptyStateProps = { title: string; message?: string; action?: ReactNode };

export function EmptyState({ title, message, action }: EmptyStateProps) {
  return (
    <div className="rounded-lg border border-dashed border-slate-300 p-6 text-center">
      <p className="font-medium text-slate-800">{title}</p>
      {message ? <p className="mt-1 text-sm text-slate-600">{message}</p> : null}
      {action ? <div className="mt-3">{action}</div> : null}
    </div>
  );
}
