import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

import { resetDatabase } from "./support/db";

const BLOCKING_IMPACTS = new Set(["critical", "serious"]);

test.beforeEach(() => {
  resetDatabase();
});

test("E12 /transactions has no critical or serious accessibility violations", async ({ page }) => {
  await page.goto("/transactions");
  await page.getByRole("button", { name: "Sync now" }).click();
  await expect(page.getByText(/Added 10/)).toBeVisible();
  const results = await new AxeBuilder({ page }).analyze();
  const blocking = results.violations.filter((v) => BLOCKING_IMPACTS.has(v.impact ?? ""));
  expect(blocking.map((v) => `${v.id}: ${v.help}`)).toEqual([]);
});
