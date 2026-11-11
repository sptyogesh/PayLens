"use client";

import type { ChangeEvent } from "react";
import { useId, useState } from "react";

import { PDF_ACCEPT } from "@/lib/constants";

import type { FileLimits } from "./checkFiles";
import { checkFiles, DEFAULT_FILE_LIMITS } from "./checkFiles";
import { FileErrors } from "./FileErrors";

const INPUT_CLASS =
  "block w-full max-w-full text-sm text-slate-800 file:mr-3 file:rounded-md file:border-0 file:bg-blue-700 file:px-4 file:py-2 file:text-sm file:font-medium file:text-white hover:file:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-60";

export type FileUploadProps = {
  label: string;
  hint?: string;
  /** Called with the files that passed the type and size checks (never with an empty list). */
  onFiles: (files: File[]) => void;
  disabled?: boolean;
  limits?: FileLimits;
};

/** Check each picked file; pass on the valid ones and keep a message per rejected one. */
function useFileCheck(limits: FileLimits, onFiles: (files: File[]) => void) {
  const [errors, setErrors] = useState<string[]>([]);
  function handleChange(event: ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files ?? []);
    event.target.value = "";
    const result = checkFiles(files, limits);
    setErrors(result.errors);
    if (result.valid.length > 0) onFiles(result.valid);
  }
  return { errors, handleChange };
}

/** A labelled PDF picker (several files) with per-file type and size checks in the browser. */
export function FileUpload({
  label,
  hint,
  onFiles,
  disabled = false,
  limits = DEFAULT_FILE_LIMITS,
}: FileUploadProps) {
  const inputId = useId();
  const hintId = useId();
  const { errors, handleChange } = useFileCheck(limits, onFiles);

  return (
    <div className="space-y-2">
      <label htmlFor={inputId} className="block text-sm font-medium text-slate-900">
        {label}
      </label>
      <input
        id={inputId}
        type="file"
        accept={PDF_ACCEPT}
        multiple
        disabled={disabled}
        aria-describedby={hint ? hintId : undefined}
        onChange={handleChange}
        className={INPUT_CLASS}
      />
      {hint ? (
        <p id={hintId} className="text-xs text-slate-600">
          {hint}
        </p>
      ) : null}
      <FileErrors errors={errors} />
    </div>
  );
}
