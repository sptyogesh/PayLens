import type { TextareaHTMLAttributes } from "react";
import { useId } from "react";

import { FIELD_CLASS } from "../TextField";

export type TextAreaProps = Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, "onChange"> & {
  label: string;
  value: string;
  /** Help text under the field (e.g. a character counter), linked as the description. */
  hint?: string | undefined;
  error?: string | undefined;
  onValueChange: (value: string) => void;
};

/** A labelled multi-line input; the multi-line sibling of TextField. */
export function TextArea({
  label,
  value,
  hint,
  error,
  onValueChange,
  className = "",
  ...rest
}: TextAreaProps) {
  const fieldId = useId();
  const hintId = useId();
  const errorId = useId();
  const describedBy = [hint ? hintId : null, error ? errorId : null].filter(Boolean).join(" ");
  return (
    <div className={`text-sm font-medium ${className}`}>
      <label htmlFor={fieldId}>{label}</label>
      <textarea
        {...rest}
        id={fieldId}
        className={`${FIELD_CLASS} resize-y`}
        value={value}
        aria-invalid={Boolean(error)}
        aria-describedby={describedBy || undefined}
        onChange={(event) => {
          onValueChange(event.target.value);
        }}
      />
      {hint ? (
        <span id={hintId} className="mt-1 block text-xs font-normal text-slate-600">
          {hint}
        </span>
      ) : null}
      {error ? (
        <span id={errorId} className="mt-1 block text-xs text-red-800">
          {error}
        </span>
      ) : null}
    </div>
  );
}
