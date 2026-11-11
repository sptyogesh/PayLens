import { describe, expect, it } from "vitest";

import { publicEnvProblems } from "./check-public-env";

const RENDER_ENV = {
  NEXT_PUBLIC_API_URL: "https://paylens-api.onrender.com",
  NEXT_PUBLIC_PAYPAL_MODE: "http",
  NEXT_PUBLIC_PAYPAL_CLIENT_ID: "sandbox-client-id",
};

describe("publicEnvProblems", () => {
  it("accepts a complete Render build", () => {
    expect(publicEnvProblems(RENDER_ENV)).toEqual([]);
  });

  it("accepts the E2E build (fake PayPal, localhost API)", () => {
    expect(
      publicEnvProblems({
        NEXT_PUBLIC_API_URL: "http://localhost:8001",
        NEXT_PUBLIC_PAYPAL_MODE: "fake",
        NEXT_PUBLIC_PAYPAL_CLIENT_ID: "test",
      }),
    ).toEqual([]);
  });

  it("accepts a local real-mode build against localhost over http", () => {
    expect(
      publicEnvProblems({ ...RENDER_ENV, NEXT_PUBLIC_API_URL: "http://127.0.0.1:8000" }),
    ).toEqual([]);
  });

  it.each([
    [{ NEXT_PUBLIC_API_URL: undefined }, "NEXT_PUBLIC_API_URL is not set"],
    [{ NEXT_PUBLIC_API_URL: "paylens-api.onrender.com" }, "not a full URL"],
    [{ NEXT_PUBLIC_API_URL: "http://paylens-api.onrender.com" }, "must use https://"],
    [{ NEXT_PUBLIC_API_URL: "ftp://paylens-api.onrender.com" }, "must be http(s)"],
    [{ NEXT_PUBLIC_API_URL: "https://paylens-api.onrender.com/" }, "must not end with '/'"],
    [{ NEXT_PUBLIC_PAYPAL_CLIENT_ID: "" }, "NEXT_PUBLIC_PAYPAL_CLIENT_ID is not set"],
    [{ NEXT_PUBLIC_PAYPAL_MODE: undefined }, "NEXT_PUBLIC_PAYPAL_MODE must be"],
    [{ NEXT_PUBLIC_PAYPAL_MODE: "live" }, "NEXT_PUBLIC_PAYPAL_MODE must be"],
  ])("reports %o", (override, message) => {
    const problems = publicEnvProblems({ ...RENDER_ENV, ...override });
    expect(problems.some((problem) => problem.includes(message))).toBe(true);
  });

  it("reports an empty environment as missing mode and API URL", () => {
    expect(publicEnvProblems({})).toEqual([
      "NEXT_PUBLIC_PAYPAL_MODE must be http (real sandbox) or fake (tests).",
      "NEXT_PUBLIC_API_URL is not set (the backend URL, e.g. https://paylens-api.onrender.com).",
    ]);
  });
});
