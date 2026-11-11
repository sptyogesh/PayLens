"use client";

import { useCallback, useEffect, useState } from "react";
import { z } from "zod";

import { apiGet } from "@/lib/api/client";
import { retryWhileWaking } from "@/lib/api/wake";
import { HEALTH_PATH, WAKE_NOTICE_DELAY_MS } from "@/lib/constants";

/** checking: no notice yet; waking: still starting after the delay; ready; down: never answered. */
export type WakeState = "checking" | "waking" | "ready" | "down";

const HealthSchema = z.object({ status: z.literal("ok") });

/** Pings /health once per mount (and on retry) while the free-tier backend may be asleep. */
export function useBackendWake(): { state: WakeState; retry: () => void } {
  const [state, setState] = useState<WakeState>("checking");
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let active = true;
    const timer = setTimeout(() => {
      if (active) setState((current) => (current === "checking" ? "waking" : current));
    }, WAKE_NOTICE_DELAY_MS);
    const ping = async (): Promise<void> => {
      let next: WakeState = "ready";
      try {
        await retryWhileWaking(() => apiGet(HEALTH_PATH, HealthSchema));
      } catch {
        next = "down";
      }
      if (active) setState(next);
    };
    void ping();
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [attempt]);

  const retry = useCallback(() => {
    setState("checking");
    setAttempt((value) => value + 1);
  }, []);

  return { state, retry };
}
