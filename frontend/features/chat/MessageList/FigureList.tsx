import { useId } from "react";

import { MoneyText } from "@/components/ui/MoneyText";
import type { Figure } from "@/lib/api/chat-schemas";
import { CHAT_TEXT } from "@/lib/constants";
import { formatPercent } from "@/lib/format";

/** Grandchild: the figures behind an answer, taken from tool results by the backend. */
export function FigureList({ figures }: { figures: Figure[] }) {
  const headingId = useId();
  if (figures.length === 0) return null;
  return (
    <div className="mt-3 border-t border-slate-200 pt-2">
      <h3 id={headingId} className="text-xs font-semibold tracking-wide text-slate-700 uppercase">
        {CHAT_TEXT.basedOn}
      </h3>
      <ul aria-labelledby={headingId} className="mt-1 space-y-1 text-sm">
        {figures.map((figure, index) => (
          <li key={`${figure.label}-${figure.period}-${String(index)}`} className="break-words">
            <span className="text-slate-700">{figure.label}: </span>
            <FigureValue figure={figure} />
            <span className="block text-xs text-slate-600">{figure.period}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function FigureValue({ figure }: { figure: Figure }) {
  if (figure.kind === "money" && figure.currency !== null) {
    return (
      <MoneyText
        amount={figure.value}
        currency={figure.currency}
        gainWhenNegative={figure.label.includes(CHAT_TEXT.fxLossMarker)}
        className="font-medium"
      />
    );
  }
  const text = figure.kind === "percent" ? formatPercent(figure.value) : figure.value;
  return <span className="font-medium tabular-nums">{text}</span>;
}
