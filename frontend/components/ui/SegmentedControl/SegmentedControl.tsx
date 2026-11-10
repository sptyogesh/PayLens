import { useId } from "react";

export type SegmentedOption<T extends string> = { value: T; label: string };

export type SegmentedControlProps<T extends string> = {
  /** Accessible name of the group (visually hidden). */
  label: string;
  options: readonly SegmentedOption<T>[];
  value: T;
  onChange: (value: T) => void;
};

const SEGMENT_CLASS =
  "cursor-pointer rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium " +
  "text-slate-700 has-[:checked]:border-slate-900 has-[:checked]:bg-slate-900 " +
  "has-[:checked]:text-white has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-blue-600 " +
  "has-[:focus-visible]:ring-offset-1";

/** A single-choice control (native radio group) styled as segmented buttons. */
export function SegmentedControl<T extends string>({
  label,
  options,
  value,
  onChange,
}: SegmentedControlProps<T>) {
  const name = useId();
  return (
    <fieldset>
      <legend className="sr-only">{label}</legend>
      <div className="flex flex-wrap gap-2">
        {options.map((option) => (
          <label key={option.value} className={SEGMENT_CLASS}>
            <input
              type="radio"
              className="sr-only"
              name={name}
              value={option.value}
              checked={option.value === value}
              onChange={() => {
                onChange(option.value);
              }}
            />
            {option.label}
          </label>
        ))}
      </div>
    </fieldset>
  );
}
