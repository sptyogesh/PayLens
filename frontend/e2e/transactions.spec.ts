import { expect, test } from "@playwright/test";

import { API_URL, formatInr, resetDatabase, seedDemo } from "./support/db";

test.beforeEach(() => {
  resetDatabase();
});

test("E2 Sync now stores sandbox payments once, with a source badge on every row (E3)", async ({
  page,
}) => {
  await page.goto("/transactions");
  await expect(page.getByText("Demo mode — PayPal sandbox data")).toBeVisible();
  await expect(page.getByText("No transactions yet")).toBeVisible();

  await page.getByRole("button", { name: "Sync now" }).click();
  await expect(page.getByText("Added 10 · Updated 0 · Skipped 2 · Flagged 0")).toBeVisible();
  const grid = page.getByRole("region", { name: "Transactions" });
  await expect(grid.getByText("PayPal sandbox")).toHaveCount(10);

  await page.getByRole("button", { name: "Sync now" }).click();
  await expect(page.getByText("Added 0 · Updated 10 · Skipped 2 · Flagged 0")).toBeVisible();
  await expect(grid.getByText("PayPal sandbox")).toHaveCount(10);
});

test("E10 backend unavailable shows an error with retry", async ({ page }) => {
  await page.route(`${API_URL}/transactions*`, (route) => route.abort());
  await page.goto("/transactions");
  await expect(
    page.getByRole("alert").filter({ hasText: "Cannot reach the PayLens server" }),
  ).toBeVisible();
  await page.unroute(`${API_URL}/transactions*`);
  await page.getByRole("button", { name: "Try again" }).click();
  await expect(page.getByText("No transactions yet")).toBeVisible();
});

test("E11 no horizontal page scroll", async ({ page }) => {
  await page.goto("/transactions");
  await page.getByRole("button", { name: "Sync now" }).click();
  await expect(page.getByText(/Added 10/)).toBeVisible();
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  expect(overflow).toBeLessThanOrEqual(0);
});

test("FR-050 seeded and synced rows show their own source badges side by side", async ({
  page,
}) => {
  seedDemo();
  await page.goto("/transactions");
  const grid = page.getByRole("region", { name: "Transactions" });
  await expect(grid.getByText("Demo seed")).toHaveCount(24);
  await page.getByRole("button", { name: "Sync now" }).click();
  await expect(page.getByText(/Added 10/)).toBeVisible();
  await expect(grid.getByText("PayPal sandbox")).toHaveCount(10);
  await expect(grid.getByText("Demo seed")).toHaveCount(24);
});

test("E3/E4 seeded rows show INR leakage, simulated label, and sort by total leakage", async ({
  page,
  request,
}) => {
  seedDemo();
  const body = (await (await request.get(`${API_URL}/transactions?limit=200`)).json()) as {
    items: { leakage: { total_leakage_inr: { amount: string } } | null }[];
  };
  const totals = body.items.map((item) => item.leakage?.total_leakage_inr.amount ?? "");
  expect(totals.every((amount) => amount !== "")).toBe(true);
  const largest = [...totals].sort((a, b) => Number(b) - Number(a))[0] ?? "";
  const formatted = formatInr(largest);

  await page.goto("/transactions");
  const grid = page.getByRole("region", { name: "Transactions" });
  await expect(grid.getByText("Demo seed")).toHaveCount(24);
  await expect(
    grid.getByRole("columnheader", { name: /PayPal rate \(Simulated \(sandbox\)\)/ }),
  ).toBeVisible();

  const header = grid.getByRole("columnheader", { name: /^Total leakage/ });
  await header.click();
  await header.click();
  await expect(header).toHaveAttribute("aria-sort", "descending");
  await expect(grid.locator('[role="row"][aria-rowindex="2"]')).toContainText(formatted);
});
