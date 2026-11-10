"use client";

import { useCallback } from "react";

import { useApi } from "@/hooks/useApi";
import { useMutation } from "@/hooks/useMutation";
import type { ApiError } from "@/lib/api/client";
import type { SyncRun } from "@/lib/api/schemas";
import { LastSyncSchema, SyncRunSchema } from "@/lib/api/schemas";

export type SyncState = {
  lastRun: SyncRun | null;
  running: boolean;
  error: ApiError | null;
  syncNow: () => Promise<void>;
};

/** Last sync result plus a Sync now action. `onSynced` runs after every finished sync. */
export function useSync(onSynced: () => void): SyncState {
  const last = useApi("/sync/last", LastSyncSchema);
  const { state, run } = useMutation("/sync", SyncRunSchema);

  const syncNow = useCallback(async () => {
    const result = await run({});
    if (result) onSynced();
  }, [run, onSynced]);

  const latest = state.status === "success" ? state.data : null;
  return {
    lastRun: latest ?? (last.status === "success" ? last.data : null),
    running: state.status === "running",
    error: state.status === "error" ? state.error : null,
    syncNow,
  };
}
