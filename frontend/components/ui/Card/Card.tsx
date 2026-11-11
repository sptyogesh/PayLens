import type { ReactNode } from "react";

export type CardProps = { title?: string; children: ReactNode; className?: string };

export function Card({ title, children, className = "" }: CardProps) {
  return (
    <section className={`rounded-lg border border-slate-200 bg-white p-4 shadow-sm ${className}`}>
      {title ? <h2 className="mb-3 text-base font-semibold text-slate-900">{title}</h2> : null}
      {children}
    </section>
  );
}
