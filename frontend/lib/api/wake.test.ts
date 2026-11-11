import { WAKE_RETRY_DELAYS_MS } from "../constants";
import { ApiError } from "./client";
import { isWakeError, retryWhileWaking, wakeDelay } from "./wake";

const WINDOW_MS = 30_000;
const BAD_GATEWAY = 502;
const SERVICE_UNAVAILABLE = 503;
const GATEWAY_TIMEOUT = 504;
const SERVER_ERROR = 500;
const NOT_FOUND = 404;
const FAILURES_BEFORE_SUCCESS = 3;

const network = () => new ApiError(0, "NETWORK_ERROR", "down");
const http = (status: number) => new ApiError(status, "HTTP_ERROR", "x");

/** A fake clock: sleeping moves time forward and is recorded. */
function clock() {
  const state = { time: 0, slept: [] as number[] };
  return {
    state,
    now: () => state.time,
    sleep: (ms: number) => {
      state.slept.push(ms);
      state.time += ms;
      return Promise.resolve();
    },
  };
}

function failing(times: number, error: () => ApiError) {
  const calls = { count: 0 };
  const run = () => {
    calls.count += 1;
    return calls.count <= times ? Promise.reject(error()) : Promise.resolve("ok");
  };
  return { calls, run };
}

describe("isWakeError", () => {
  it.each([
    [network(), true],
    [http(BAD_GATEWAY), true],
    [http(SERVICE_UNAVAILABLE), true],
    [http(GATEWAY_TIMEOUT), true],
    [http(SERVER_ERROR), false],
    [http(NOT_FOUND), false],
    [new ApiError(0, "TIMEOUT", "slow"), false],
    [new Error("other"), false],
  ])("%o → %s", (error, expected) => {
    expect(isWakeError(error)).toBe(expected);
  });
});

describe("retryWhileWaking", () => {
  it("retries wake errors with the backoff delays until it succeeds", async () => {
    const fake = clock();
    const { calls, run } = failing(FAILURES_BEFORE_SUCCESS, network);
    await expect(retryWhileWaking(run, { windowMs: WINDOW_MS, ...fake })).resolves.toBe("ok");
    expect(calls.count).toBe(FAILURES_BEFORE_SUCCESS + 1);
    expect(fake.state.slept).toEqual(WAKE_RETRY_DELAYS_MS.slice(0, FAILURES_BEFORE_SUCCESS));
  });

  it("does not retry other errors", async () => {
    const fake = clock();
    const { calls, run } = failing(1, () => http(SERVER_ERROR));
    await expect(retryWhileWaking(run, { windowMs: WINDOW_MS, ...fake })).rejects.toMatchObject({
      status: SERVER_ERROR,
    });
    expect(calls.count).toBe(1);
  });

  it("gives up with the last error when the window ends", async () => {
    const fake = clock();
    const { run } = failing(Number.POSITIVE_INFINITY, () => http(SERVICE_UNAVAILABLE));
    await expect(retryWhileWaking(run, { windowMs: WINDOW_MS, ...fake })).rejects.toMatchObject({
      status: SERVICE_UNAVAILABLE,
    });
    expect(fake.state.time).toBeLessThanOrEqual(WINDOW_MS);
  });

  it("makes one attempt when the window is 0", async () => {
    const { calls, run } = failing(1, network);
    await expect(retryWhileWaking(run, { windowMs: 0 })).rejects.toBeInstanceOf(ApiError);
    expect(calls.count).toBe(1);
  });

  it("repeats the last delay after the listed ones", () => {
    const last = WAKE_RETRY_DELAYS_MS[WAKE_RETRY_DELAYS_MS.length - 1];
    expect(wakeDelay(WAKE_RETRY_DELAYS_MS.length + FAILURES_BEFORE_SUCCESS)).toBe(last);
  });
});
