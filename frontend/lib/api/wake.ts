/**
 * Retry safe (GET) requests while a sleeping backend starts: a network error or 502/503/504 is
 * retried with backoff until the wake window ends; any other error is returned at once.
 * Never use for POSTs (payments, sync, chat must not run twice).
 */
import { WAKE_HTTP_STATUSES, WAKE_RETRY_DELAYS_MS, WAKE_WINDOW_MS } from "../constants";
import { ApiError } from "./client";

export type Sleep = (ms: number) => Promise<void>;
export type WakeOptions = { windowMs?: number; sleep?: Sleep; now?: () => number };

/** Window used when no option is given. Unit tests set it to 0 (test/setup.ts). */
export const wakeDefaults = { windowMs: WAKE_WINDOW_MS };

const LAST_DELAY_MS = WAKE_RETRY_DELAYS_MS[WAKE_RETRY_DELAYS_MS.length - 1] ?? 0;

const realSleep: Sleep = (ms) =>
  new Promise((resolve) => {
    setTimeout(resolve, ms);
  });

export function isWakeError(error: unknown): boolean {
  if (!(error instanceof ApiError)) return false;
  return error.code === "NETWORK_ERROR" || WAKE_HTTP_STATUSES.includes(error.status);
}

export function wakeDelay(attempt: number): number {
  return WAKE_RETRY_DELAYS_MS[attempt] ?? LAST_DELAY_MS;
}

export function retryWhileWaking<T>(run: () => Promise<T>, options: WakeOptions = {}): Promise<T> {
  const { windowMs = wakeDefaults.windowMs, sleep = realSleep, now = Date.now } = options;
  const deadline = now() + windowMs;
  const attempt = async (count: number): Promise<T> => {
    try {
      return await run();
    } catch (error) {
      const delay = wakeDelay(count);
      if (!isWakeError(error) || now() + delay > deadline) throw error;
      await sleep(delay);
      return attempt(count + 1);
    }
  };
  return attempt(0);
}
