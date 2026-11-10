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

/** GET `path`, validate with `schema`, expose loading / success / error and reload(). */
export function useApi<T>(
  path: string,
  schema: z.ZodType<T>,
): ApiState<T> & { reload: () => void } {
  const [state, setState] = useState<ApiState<T>>({ status: "loading" });
  const [version, setVersion] = useState(0);

  useEffect(() => {
    let active = true;
    apiGet(path, schema).then(
      (data) => {
        if (active) setState({ status: "success", data });
      },
      (error: unknown) => {
        if (active) setState({ status: "error", error: toApiError(error) });
      },
    );
    return () => {
      active = false;
    };
  }, [path, schema, version]);

  const reload = useCallback(() => {
    setState({ status: "loading" });
    setVersion((value) => value + 1);
  }, []);

  return { ...state, reload };
}
