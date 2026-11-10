import { DISCLAIMERS } from "@/lib/constants";

export type DisclaimerKind = keyof typeof DISCLAIMERS;

/** Either a standard disclaimer from DISCLAIMERS, or text the caller already built. */
export type DisclaimerProps = { kind: DisclaimerKind } | { text: string };

export function Disclaimer(props: DisclaimerProps) {
  const text = "kind" in props ? DISCLAIMERS[props.kind] : props.text;
  return (
    <p role="note" className="rounded-md bg-slate-100 px-3 py-2 text-xs text-slate-700">
      {text}
    </p>
  );
}
