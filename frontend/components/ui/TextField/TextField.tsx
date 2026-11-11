import type { InputHTMLAttributes } from "react";
import { useId } from "react";

export const FIELD_CLASS = "mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm";

export type TextFieldProps = Omit<InputHTMLAttributes<HTMLInputElement>, "onChange"> & {
  label: string;
  value: string;
  error?: string | undefined;
  onValueChange: (value: string) => void;
};

/** A labelled text input with an accessible error message. */
export function TextField({
  label,
  value,
  error,
  onValueChange,
  className = "",
  ...rest
}: TextFieldProps) {
  const errorId = useId();
  return (
    <label className={`text-sm font-medium ${className}`}>
      {label}
      <input
        {...rest}
        className={FIELD_CLASS}
        value={value}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? errorId : undefined}
        onChange={(event) => {
          onValueChange(event.target.value);
        }}
      />
      {error ? (
        <span id={errorId} className="mt-1 block text-xs text-red-800">
          {error}
        </span>
      ) : null}
    </label>
  );
}
