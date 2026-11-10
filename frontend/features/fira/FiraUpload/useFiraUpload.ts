"use client";

import { useCallback, useState } from "react";

import { toApiError } from "@/hooks/useApi";
import { apiPostBytes } from "@/lib/api/client";
import type { FiraUploadResult } from "@/lib/api/fira-schemas";
import { FiraUploadOutSchema } from "@/lib/api/fira-schemas";
import { FIRA_UPLOAD_TIMEOUT_MS, PDF_CONTENT_TYPE } from "@/lib/constants";

import { FIRA_UPLOAD_PATH } from "../useFira";

export type UploadProgress = { current: number; total: number };

/** One request per file; a failed request becomes a "failed" result so the others still run. */
async function uploadOne(file: File): Promise<FiraUploadResult> {
  const path = `${FIRA_UPLOAD_PATH}?file_name=${encodeURIComponent(file.name)}`;
  try {
    const out = await apiPostBytes(path, file, PDF_CONTENT_TYPE, FiraUploadOutSchema, {
      timeoutMs: FIRA_UPLOAD_TIMEOUT_MS,
    });
    return out.result;
  } catch (error) {
    const { message } = toApiError(error);
    return { file_name: file.name, outcome: "failed", message, fira_id: null, status: null };
  }
}

/** Upload files one after another, collect each result, then call `onDone` once. */
export function useFiraUpload(onDone: () => void) {
  const [progress, setProgress] = useState<UploadProgress | null>(null);
  const [results, setResults] = useState<FiraUploadResult[]>([]);

  const upload = useCallback(
    async (files: File[]): Promise<void> => {
      setResults([]);
      for (const [index, file] of files.entries()) {
        setProgress({ current: index + 1, total: files.length });
        const result = await uploadOne(file);
        setResults((previous) => [...previous, result]);
      }
      setProgress(null);
      onDone();
    },
    [onDone],
  );

  return { progress, results, upload };
}
