import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

import { resetDatabase } from "./support/db";

const BLOCKING_IMPACTS = new Set(["critical", "serious"]);

test.beforeEach(() => {
  resetDatabase();
});

test("fake checkout of 50.00 USD is confirmed and listed as PayPal sandbox", async ({ page }) => {
  await page.goto("/pay");
  await expect(page.getByText(/Sandbox demo — no real money/)).toBeVisible();
  await page.getByLabel("Amount").fill("50.00");
  await page.getByLabel("Currency").selectOption("USD");
  await page.getByLabel("Description (optional)").fill("Logo design");
  await page.getByRole("button", { name: "Pay (test mode)" }).click();

  const confirmation = page.getByRole("status").filter({ hasText: "Payment received" });
  await expect(confirmation).toContainText("$50.00");
  const transactionId = await confirmation.getByTestId("transaction-id").textContent();
  expect(transactionId).toMatch(/^FAKECAPTURE\d+$/);

  await page.getByRole("link", { name: "Transactions" }).click();
  const grid = page.getByRole("region", { name: "Transactions" });
  await expect(grid.getByText("Ava Stone")).toBeVisible();
  await expect(grid.getByText("PayPal sandbox")).toHaveCount(1);
});

test("invalid amount keeps the pay button disabled", async ({ page }) => {
  await page.goto("/pay");
  const button = page.getByRole("button", { name: "Pay (test mode)" });
  await expect(button).toBeDisabled();
  await page.getByLabel("Amount").fill("1.234");
  await expect(page.getByText(/at most 2 decimals/)).toBeVisible();
  await expect(button).toBeDisabled();
});

test("declined payment shows 'No payment was made'", async ({ page }) => {
  await page.goto("/pay");
  await page.getByLabel("Amount").fill("13.13");
  await page.getByRole("button", { name: "Pay (test mode)" }).click();
  await expect(page.getByRole("alert").filter({ hasText: "No payment was made." })).toBeVisible();
});

test("E11 /pay has no horizontal page scroll and E12 no blocking a11y violations", async ({
  page,
}) => {
  await page.goto("/pay");
  await expect(page.getByRole("button", { name: "Pay (test mode)" })).toBeVisible();
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  expect(overflow).toBeLessThanOrEqual(0);
  const results = await new AxeBuilder({ page }).analyze();
  const blocking = results.violations.filter((v) => BLOCKING_IMPACTS.has(v.impact ?? ""));
  expect(blocking.map((v) => `${v.id}: ${v.help}`)).toEqual([]);
});
