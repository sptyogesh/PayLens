import { FIRA_LABELS, SOURCE_LABELS } from "@/lib/constants";

const BADGES = {
  paypal_sandbox: { label: SOURCE_LABELS.paypal_sandbox, className: "bg-blue-100 text-blue-900" },
  demo_seed: { label: SOURCE_LABELS.demo_seed, className: "bg-amber-100 text-amber-900" },
  matched: { label: FIRA_LABELS.matched, className: "bg-green-100 text-green-900" },
  needs_review: { label: FIRA_LABELS.needs_review, className: "bg-orange-100 text-orange-900" },
  missing: { label: FIRA_LABELS.missing, className: "bg-red-100 text-red-900" },
} as const;

export type BadgeVariant = keyof typeof BADGES;

export function Badge({ variant }: { variant: BadgeVariant }) {
  const { label, className } = BADGES[variant];
  return (
    <span
      data-variant={variant}
      className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${className}`}
    >
      {label}
    </span>
  );
}
