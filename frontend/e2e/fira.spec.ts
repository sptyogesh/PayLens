import AxeBuilder from "@axe-core/playwright";
import type { Page } from "@playwright/test";
import { expect, test } from "@playwright/test";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { resetDatabase, seedDemo } from "./support/db";
import { samplePdfs, uploadAll, uploadBatch } from "./support/fira";

const SAMPLE_COUNT = 21;
const MOBILE_VIEWPORT = { width: 390, height: 844 };
const BLOCKING_IMPACTS = new Set(["critical", "serious"]);

const card = (page: Page, name: string) => page.getByRole("group", { name, exact: true });

test.beforeEach(() => {
  resetDatabase();
  seedDemo();
});

test("E7 uploading the sample FIRAs matches 19, flags 2 for review and 3 payments missing", async ({
  page,
}) => {
  const files = samplePdfs();
  expect(files).toHaveLength(SAMPLE_COUNT);
  await page.goto("/fira");
  await uploadAll(page, files);
  await expect(card(page, "Matched")).toContainText("19");
  await expect(card(page, "Needs review")).toContainText("2");
  await expect(card(page, "Payments missing a FIRA")).toContainText("3");
  const missing = page.getByRole("region", { name: "Payments missing a FIRA" });
  await expect(missing.getByText(/^SEED-002[234]$/)).toHaveCount(3);

  await page.goto("/transactions");
  const grid = page.getByRole("region", { name: "Transactions" });
  await expect(grid.getByText("Demo seed")).toHaveCount(24);
  await expect(grid.getByText("Missing", { exact: true })).toHaveCount(3);
  await expect(grid.getByText("Needs review", { exact: true })).toHaveCount(2);
  await expect(grid.getByText("Matched", { exact: true })).toHaveCount(19);
});

test("E8 a non-PDF is rejected in the browser and nothing is uploaded", async ({ page }) => {
  const uploads: string[] = [];
  page.on("request", (request) => {
    if (request.url().includes("/fira/upload")) uploads.push(request.url());
  });
  const textFile = join(mkdtempSync(join(tmpdir(), "paylens-fira-txt-")), "notes.txt");
  writeFileSync(textFile, "not a pdf");

  await page.goto("/fira");
  await expect(card(page, "Matched")).toContainText("0");
  await page.getByLabel("FIRA PDFs").setInputFiles(textFile);
  await expect(page.getByRole("alert").filter({ hasText: "notes.txt is not a PDF" })).toBeVisible();
  await expect(page.getByRole("list", { name: "Upload results" })).toHaveCount(0);
  expect(uploads).toEqual([]);
});

test("E8 the same FIRA uploaded twice is rejected as a duplicate", async ({ page }) => {
  const [first] = samplePdfs();
  if (!first) throw new Error("no FIRA samples generated");
  await page.goto("/fira");
  await uploadBatch(page, [first]);
  const results = page.getByRole("list", { name: "Upload results" });
  await expect(results.getByText("Stored", { exact: true })).toBeVisible();
  await uploadBatch(page, [first]);
  await expect(results.getByText("Duplicate", { exact: true })).toBeVisible();
  await expect(card(page, "Matched")).toContainText("1");
});

test("E11 /fira has no horizontal page scroll at 390 px", async ({ page }) => {
  await page.setViewportSize(MOBILE_VIEWPORT);
  await page.goto("/fira");
  await expect(card(page, "Payments missing a FIRA")).toBeVisible();
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  expect(overflow).toBeLessThanOrEqual(0);
});

test("E12 /fira has no critical or serious accessibility violations", async ({ page }) => {
  await page.goto("/fira");
  await expect(card(page, "Payments missing a FIRA")).toBeVisible();
  const results = await new AxeBuilder({ page }).analyze();
  const blocking = results.violations.filter((v) => BLOCKING_IMPACTS.has(v.impact ?? ""));
  expect(blocking.map((v) => `${v.id}: ${v.help}`)).toEqual([]);
});
