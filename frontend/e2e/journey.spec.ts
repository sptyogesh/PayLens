/**
 * Phase 1A journey across every feature (hardening step 1): seed → /pay (test mode) → Sync now →
 * dashboard → chat answer equals the dashboard → FIRA upload → CA report equals the dashboard.
 * The backend runs in fake modes (PayPal, FX, LLM); numbers are compared with the API, never
 * recomputed here.
 */
import type { Page } from "@playwright/test";
import { expect, test } from "@playwright/test";
import { readFile } from "node:fs/promises";

import { API_URL, formatInr, formatReportInr, resetDatabase, seedDemo } from "./support/db";
import { uploadSampleFiras } from "./support/fira";

const JOURNEY_TIMEOUT_MS = 180_000;
/** The sync result line, e.g. matches "Added 10 · Updated 1"; rejects "Sync failed". */
const SYNC_RESULT = /Added \d+ · Updated \d+/;

type Money = { amount: string };
type Dashboard = {
  totals: { total_leakage_inr: Money; fx_loss_inr: Money; payment_count: number };
};

async function allTime(page: Page): Promise<Dashboard> {
  const response = await page.request.get(`${API_URL}/dashboard?period=all_time`);
  return (await response.json()) as Dashboard;
}

async function payInTestMode(page: Page): Promise<void> {
  await page.goto("/pay");
  await page.getByLabel("Amount").fill("75.00");
  await page.getByLabel("Currency").selectOption("USD");
  await page.getByRole("button", { name: "Pay (test mode)" }).click();
  await expect(page.getByRole("status").filter({ hasText: "Payment received" })).toBeVisible();
}

async function syncNow(page: Page): Promise<void> {
  await page.goto("/transactions");
  await page.getByRole("button", { name: "Sync now" }).click();
  await expect(page.getByText(SYNC_RESULT)).toBeVisible();
}

test("Phase 1A journey: pay, sync, dashboard, chat, FIRA and CA report agree", async ({
  page,
}, testInfo) => {
  test.skip(
    testInfo.project.name === "mobile",
    "one full journey is enough; pages are checked at 390 px elsewhere",
  );
  test.setTimeout(JOURNEY_TIMEOUT_MS);
  resetDatabase();
  seedDemo();

  await payInTestMode(page);
  await syncNow(page);

  const dashboard = await allTime(page);
  await page.goto("/");
  await page.getByText("All time", { exact: true }).click();
  const total = formatInr(dashboard.totals.total_leakage_inr.amount);
  await expect(page.getByRole("group", { name: "Total leakage" })).toContainText(total);

  await page.goto("/chat");
  await page.getByLabel("Your question").fill("How much FX loss in all time?");
  await page.getByRole("button", { name: "Send" }).click();
  const answer = page.getByRole("article", { name: "PayLens assistant" }).first();
  const figures = answer.getByRole("list", { name: "Based on" });
  await expect(figures.getByRole("listitem").filter({ hasText: "FX loss" })).toContainText(
    formatInr(dashboard.totals.fx_loss_inr.amount),
  );

  await uploadSampleFiras(page);

  await page.goto("/");
  await page.getByText("All time", { exact: true }).click();
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "Download CA report" }).click();
  const raw = (await readFile(await (await downloadPromise).path())).toString("latin1");
  expect(raw.startsWith("%PDF-")).toBe(true);
  expect(raw).toContain(formatReportInr(dashboard.totals.total_leakage_inr.amount));
  expect(raw).toContain("Prepared from user data");
  expect(raw).toContain(`(${String(dashboard.totals.payment_count)})`);
});
