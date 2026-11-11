"use client";

import { useCallback, useState } from "react";
import type { z } from "zod";

import type { ApiError } from "@/lib/api/client";
import { apiPost } from "@/lib/api/client";

import { toApiError } from "./useApi";

export type MutationState<T> =
  | { status: "idle" }
  | { status: "running" }
  | { status: "success"; data: T }
  | { status: "error"; error: ApiError };

/** POST to `path` on demand. Returns the data, or null when the request failed. */
export function useMutation<T>(path: string, schema: z.ZodType<T>) {
  const [state, setState] = useState<MutationState<T>>({ status: "idle" });

  const run = useCallback(
    async (body?: unknown): Promise<T | null> => {
      setState({ status: "running" });
      try {
        const data = await apiPost(path, body, schema);
        setState({ status: "success", data });
        return data;
      } catch (error) {
        setState({ status: "error", error: toApiError(error) });
        return null;
      }
    },
    [path, schema],
  );

  return { state, run };
}
