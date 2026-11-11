/**
 * Free-tier wake-up: while the backend is "asleep" (slow /health, then 503 from the proxy) the app
 * shows the waking notice, keeps loading, and then shows the dashboard without an error.
 */
import type { Route } from "@playwright/test";
import { expect, test } from "@playwright/test";

import { API_URL, resetDatabase, seedDemo } from "./support/db";

const SLEEPING_MS = 4_000; // longer than the notice delay (2.5 s)
const SERVICE_UNAVAILABLE = 503;
// The waking notice: matches "Waking up the PayLens server. Free hosting…"; rejects "PayLens".
const WAKING_TEXT = /Waking up the PayLens server/;
// /health retries (1 s, 2 s, 4 s) plus both sleeps fit well inside this.
const LOAD_TIMEOUT_MS = 16_000;
// Render's proxy answers cross-origin, so the fake answer needs the CORS header to be readable.
const CORS = { "access-control-allow-origin": "*" };

function asleepOnce(): (route: Route) => Promise<void> {
  let first = true;
  return async (route) => {
    if (!first) {
      await route.continue();
      return;
    }
    first = false;
    await new Promise((resolve) => {
      setTimeout(resolve, SLEEPING_MS);
    });
    await route.fulfill({ status: SERVICE_UNAVAILABLE, headers: CORS, body: "starting" });
  };
}

test.beforeEach(() => {
  resetDatabase();
  seedDemo();
});

test("a sleeping backend shows the waking notice, then the dashboard without an error", async ({
  page,
}) => {
  await page.route(`${API_URL}/health`, asleepOnce());
  await page.route(`${API_URL}/dashboard?*`, asleepOnce());

  await page.goto("/");
  await expect(page.getByText(WAKING_TEXT)).toBeVisible();
  await expect(page.getByRole("group", { name: "Total leakage" })).toBeVisible({
    timeout: LOAD_TIMEOUT_MS,
  });
  await expect(page.getByText(WAKING_TEXT)).toBeHidden();
  // Inside the page only: Next.js adds an empty route-announcer alert outside <main>.
  await expect(page.getByRole("main").getByRole("alert")).toHaveCount(0);
});
