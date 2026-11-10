"use client";

import { useCallback, useEffect, useState } from "react";
import type { z } from "zod";

import { ApiError, apiGet } from "@/lib/api/client";
import { MESSAGES } from "@/lib/constants";

export type ApiState<T> =
  { status: "loading" } | { status: "success"; data: T } | { status: "error"; error: ApiError };

export function toApiError(error: unknown): ApiError {
  return error instanceof ApiError ? error : new ApiError(0, "UNKNOWN", MESSAGES.genericError);
}

/**
 * GET `path`, validate with `schema`, expose loading / success / error and reload().
 * The state is keyed by path, so switching to a new path shows "loading" at once instead of
 * the previous path's data.
 */
export function useApi<T>(
  path: string,
  schema: z.ZodType<T>,
): ApiState<T> & { reload: () => void } {
  const [result, setResult] = useState<{ path: string; state: ApiState<T> } | null>(null);
  const [version, setVersion] = useState(0);

  useEffect(() => {
    let active = true;
    apiGet(path, schema).then(
      (data) => {
        if (active) setResult({ path, state: { status: "success", data } });
      },
      (error: unknown) => {
        if (active) setResult({ path, state: { status: "error", error: toApiError(error) } });
      },
    );
    return () => {
      active = false;
    };
  }, [path, schema, version]);

  const reload = useCallback(() => {
    setResult(null);
    setVersion((value) => value + 1);
  }, []);

  const state: ApiState<T> = result?.path === path ? result.state : { status: "loading" };
  return { ...state, reload };
}
