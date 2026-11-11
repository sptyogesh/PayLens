"use client";

import { ErrorState } from "@/components/ui/ErrorState";
import { Spinner } from "@/components/ui/Spinner";
import { WAKE_MESSAGES } from "@/lib/constants";

import { useBackendWake } from "./useBackendWake";

/** App-wide notice while a sleeping free-tier backend starts; nothing when it is awake. */
export function WakeNotice() {
  const { state, retry } = useBackendWake();
  if (state === "waking") {
    return (
      <div className="mb-4 rounded-lg border border-amber-200 bg-amber-50 p-3">
        <Spinner label={WAKE_MESSAGES.waking} />
      </div>
    );
  }
  if (state === "down") {
    return (
      <div className="mb-4">
        <ErrorState message={WAKE_MESSAGES.down} onRetry={retry} />
      </div>
    );
  }
  return null;
}
