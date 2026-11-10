import { DISCLAIMERS } from "@/lib/constants";

export type DisclaimerKind = keyof typeof DISCLAIMERS;

export function Disclaimer({ kind }: { kind: DisclaimerKind }) {
  return (
    <p role="note" className="rounded-md bg-slate-100 px-3 py-2 text-xs text-slate-700">
      {DISCLAIMERS[kind]}
    </p>
  );
}
