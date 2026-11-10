import { MESSAGES } from "@/lib/constants";

export function Spinner({ label = MESSAGES.loading }: { label?: string }) {
  return (
    <div role="status" className="flex items-center gap-2 text-sm text-slate-600">
      <span
        aria-hidden="true"
        className="size-4 animate-spin rounded-full border-2 border-slate-300 border-t-blue-700"
      />
      <span>{label}</span>
    </div>
  );
}
