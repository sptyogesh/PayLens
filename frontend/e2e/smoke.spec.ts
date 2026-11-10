import { expect, test } from "@playwright/test";

const API_HEALTH_URL = "http://localhost:8001/health";

test("app shell loads and the backend is healthy", async ({ page, request }) => {
  const health = await request.get(API_HEALTH_URL);
  expect(await health.json()).toEqual({ status: "ok" });
  await page.goto("/");
  await expect(page.getByRole("navigation", { name: "Main" })).toBeVisible();
});
