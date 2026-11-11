import {
  FILE_UPLOAD_TEXT,
  FIRA_MAX_BYTES,
  FIRA_MAX_FILES,
  PDF_CONTENT_TYPE,
  PDF_EXTENSION,
} from "@/lib/constants";

export type FileLimits = { maxBytes: number; maxFiles: number };
export type FileCheck = { valid: File[]; errors: string[] };

export const DEFAULT_FILE_LIMITS: FileLimits = {
  maxBytes: FIRA_MAX_BYTES,
  maxFiles: FIRA_MAX_FILES,
};

/** A PDF by name, and by type when the browser reports one. The server checks the bytes too. */
export function isPdf(file: File): boolean {
  const named = file.name.toLowerCase().endsWith(PDF_EXTENSION);
  return named && (file.type === "" || file.type === PDF_CONTENT_TYPE);
}

function problemWith(file: File, limits: FileLimits): string | null {
  if (!isPdf(file)) return FILE_UPLOAD_TEXT.notPdf(file.name);
  if (file.size === 0) return FILE_UPLOAD_TEXT.empty(file.name);
  if (file.size > limits.maxBytes) return FILE_UPLOAD_TEXT.tooLarge(file.name, limits.maxBytes);
  return null;
}

/** Split a selection into files to upload and one clear message per rejected file. */
export function checkFiles(files: File[], limits: FileLimits = DEFAULT_FILE_LIMITS): FileCheck {
  if (files.length > limits.maxFiles) {
    return { valid: [], errors: [FILE_UPLOAD_TEXT.tooMany(limits.maxFiles)] };
  }
  const valid: File[] = [];
  const errors: string[] = [];
  for (const file of files) {
    const problem = problemWith(file, limits);
    if (problem) errors.push(problem);
    else valid.push(file);
  }
  return { valid, errors };
}
