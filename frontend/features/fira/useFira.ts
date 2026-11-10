"use client";

import { useApi } from "@/hooks/useApi";
import { FiraListSchema } from "@/lib/api/fira-schemas";

export const FIRA_PATH = "/fira";
export const FIRA_UPLOAD_PATH = "/fira/upload";

export function useFira() {
  return useApi(FIRA_PATH, FiraListSchema);
}
