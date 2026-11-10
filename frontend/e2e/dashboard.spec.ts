import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

import { API_URL, formatInr as inr, resetDatabase, seedDemo } from "./support/db";

const BLOCKING_IMPACTS = new Set(["critical", "serious"]);

type Totals = { payment_count: number; total_leakage_inr: { amount: string } };

test.beforeEach(() => {
  resetDatabase();
  seedDemo();
});

test("E1 dashboard cards show the API totals in ₹ with no console errors", async ({
  page,
  request,
}) => {
  const errors: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  const api = (await (await request.get(`${API_URL}/dashboard`)).json()) as { totals: Totals };

  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Leakage dashboard" })).toBeVisible();
  const total = page.getByRole("group", { name: "Total leakage" });
  await expect(total).toContainText(inr(api.totals.total_leakage_inr.amount));
  await expect(page.getByRole("group", { name: /Total income/ })).toContainText(
    `${api.totals.payment_count} payments`,
  );
  await expect(page.getByText(/Simulated \(sandbox\): the PayPal rate/)).toBeVisible();
  expect(errors).toEqual([]);
});

test("period filter switches the totals", async ({ page, request }) => {
  const all = (await (await request.get(`${API_URL}/dashboard?period=all_time`)).json()) as {
    totals: Totals;
  };
  await page.goto("/");
  await expect(page.getByRole("group", { name: "Total leakage" })).toBeVisible();
  await page.getByText("All time", { exact: true }).click();
  await expect(page.getByRole("radio", { name: "All time" })).toBeChecked();
  await expect(page.getByRole("group", { name: /Total income/ })).toContainText(
    `${all.totals.payment_count} payments`,
  );
  await expect(page.getByRole("group", { name: "Total leakage" })).toContainText(
    inr(all.totals.total_leakage_inr.amount),
  );
});

test("E11 no horizontal scroll and E12 no blocking a11y violations on the dashboard", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.getByRole("group", { name: "Total leakage" })).toBeVisible();
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  expect(overflow).toBeLessThanOrEqual(0);
  const results = await new AxeBuilder({ page }).analyze();
  const blocking = results.violations.filter((v) => BLOCKING_IMPACTS.has(v.impact ?? ""));
  expect(blocking.map((v) => `${v.id}: ${v.help}`)).toEqual([]);
});

test("FR-032 month and client tables list every group from the API", async ({ page, request }) => {
  const body = (await (await request.get(`${API_URL}/dashboard?period=all_time`)).json()) as {
    by_month: { label: string }[];
    by_client: { label: string; totals: { total_leakage_inr: { amount: string } } }[];
  };
  await page.goto("/");
  await page.getByText("All time", { exact: true }).click();
  const months = page.getByRole("region", { name: "Leakage by month" });
  const clients = page.getByRole("region", { name: "Leakage by client" });
  // Displayed order must match the API: months newest first, clients by leakage (FR-032).
  for (const [index, month] of body.by_month.entries()) {
    const row = months.locator(`[role="row"][aria-rowindex="${index + 2}"]`);
    await expect(row).toContainText(month.label);
  }
  for (const [index, client] of body.by_client.entries()) {
    const row = clients.locator(`[role="row"][aria-rowindex="${index + 2}"]`);
    await expect(row).toContainText(client.label);
    await expect(row).toContainText(inr(client.totals.total_leakage_inr.amount));
  }
});
