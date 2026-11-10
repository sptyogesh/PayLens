import { readFile } from "node:fs/promises";

import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

import { API_URL, formatReportInr, pdfText, resetDatabase, seedDemo } from "./support/db";

const BLOCKING_IMPACTS = new Set(["critical", "serious"]);
const FILE_NAME = /^paylens-ca-report-all_time-\d{4}-\d{2}-\d{2}\.pdf$/;
const DISCLAIMER = "Prepared from user data";
/** Heading of the AI summary (backend REPORT_SUMMARY_AI_HEADING); the fake LLM always writes one. */
const AI_SUMMARY_HEADING = "Summary (AI-written from the figures below)";

type ReportData = { disclaimer: string; totals: { total_leakage_inr: { amount: string } } | null };

test.beforeEach(() => {
  resetDatabase();
  seedDemo();
});

test("E9 downloads the all-time CA report as a PDF built from the report data", async ({
  page,
  request,
}) => {
  const data = (await (
    await request.get(`${API_URL}/report/data?period=all_time`)
  ).json()) as ReportData;
  expect(data.disclaimer).toContain(DISCLAIMER);

  await page.goto("/");
  await expect(page.getByRole("group", { name: "Total leakage" })).toBeVisible();
  await page.getByText("All time", { exact: true }).click();
  await expect(page.getByRole("radio", { name: "All time" })).toBeChecked();
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "Download CA report" }).click();
  const download = await downloadPromise;

  expect(download.suggestedFilename()).toMatch(FILE_NAME);
  const raw = (await readFile(await download.path())).toString("latin1");
  expect(raw.startsWith("%PDF-")).toBe(true);
  expect(raw).toContain(DISCLAIMER);
  // The PDF is uncompressed, so its text can be searched. The number must equal the API value for
  // the same period (E9, SC-001).
  const total = data.totals?.total_leakage_inr.amount ?? "";
  expect(total).toMatch(/^\d+\.\d{2}$/);
  expect(raw).toContain(`Total leakage`);
  expect(raw).toContain(formatReportInr(total));
  await expect(page.getByRole("button", { name: "Download CA report" })).toBeEnabled();
});

test("005 US2 the downloaded report carries the AI-written summary", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("group", { name: "Total leakage" })).toBeVisible();
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "Download CA report" }).click();
  const raw = (await readFile(await (await downloadPromise).path())).toString("latin1");
  expect(pdfText(raw)).toContain(AI_SUMMARY_HEADING);
});

test("E11 no horizontal scroll and E12 no blocking a11y violations with the report button", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await expect(page.getByRole("group", { name: "Total leakage" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Download CA report" })).toBeVisible();
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  expect(overflow).toBeLessThanOrEqual(0);
  const results = await new AxeBuilder({ page }).analyze();
  const blocking = results.violations.filter((v) => BLOCKING_IMPACTS.has(v.impact ?? ""));
  expect(blocking.map((v) => `${v.id}: ${v.help}`)).toEqual([]);
});
