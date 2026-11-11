/** Free-tier wake-up: Render stops idle services; the first request starts the backend again. */
export const HEALTH_PATH = "/health";
/** How long page loads keep retrying while the backend starts (Render: usually under a minute). */
export const WAKE_WINDOW_MS = 90_000;
const FIRST_RETRY_MS = 1_000;
const SECOND_RETRY_MS = 2_000;
const THIRD_RETRY_MS = 4_000;
const STEADY_RETRY_MS = 5_000;
/** Delays between retries; the last one repeats until the window ends. */
export const WAKE_RETRY_DELAYS_MS: readonly number[] = [
  FIRST_RETRY_MS,
  SECOND_RETRY_MS,
  THIRD_RETRY_MS,
  STEADY_RETRY_MS,
];
/** Show the "waking up" notice only if /health has not answered by then (no flash when awake). */
export const WAKE_NOTICE_DELAY_MS = 2_500;
/** Answers Render's proxy gives while the service is starting. */
const BAD_GATEWAY = 502;
const SERVICE_UNAVAILABLE = 503;
const GATEWAY_TIMEOUT = 504;
export const WAKE_HTTP_STATUSES: readonly number[] = [
  BAD_GATEWAY,
  SERVICE_UNAVAILABLE,
  GATEWAY_TIMEOUT,
];

export const WAKE_MESSAGES = {
  waking:
    "Waking up the PayLens server. Free hosting sleeps when idle, so this can take up to a minute.",
  down: "The PayLens server did not start. Please try again in a minute.",
} as const;
