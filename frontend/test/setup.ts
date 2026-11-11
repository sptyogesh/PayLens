import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterAll, afterEach, beforeAll } from "vitest";

import { wakeDefaults } from "@/lib/api/wake";

import { server } from "./msw/server";

// No wake-up retries in unit tests unless a test asks for them (lib/api/wake.test.ts).
wakeDefaults.windowMs = 0;

beforeAll(() => {
  server.listen({ onUnhandledFrame: "error" });
});
afterEach(() => {
  cleanup();
  server.resetHandlers();
});
afterAll(() => {
  server.close();
});
