/** Shared FIRA helpers for E2E: generate the demo sample PDFs and upload them on /fira. */
import type { Page } from "@playwright/test";
import { expect } from "@playwright/test";
import { mkdtempSync, readdirSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { generateFiraSamples } from "./db";

/** Must match FIRA_MAX_FILES: the picker takes at most this many files at a time. */
const MAX_FILES_PER_PICK = 10;
/** AI extraction can be slow; matches FIRA_UPLOAD_TIMEOUT_MS in the app. */
const UPLOAD_TIMEOUT_MS = 60_000;

/** Generate the 21 demo FIRA PDFs (SEED-0001…0021) and return their paths, sorted. */
export function samplePdfs(): string[] {
  const dir = mkdtempSync(join(tmpdir(), "paylens-fira-"));
  generateFiraSamples(dir);
  return readdirSync(dir)
    .filter((name) => name.endsWith(".pdf"))
    .sort()
    .map((name) => join(dir, name));
}

/** Pick files on /fira and wait until every one of them has a result line. */
export async function uploadBatch(page: Page, files: string[]): Promise<void> {
  const input = page.getByLabel("FIRA PDFs");
  await input.setInputFiles(files);
  const results = page.getByRole("list", { name: "Upload results" });
  await expect(results.getByRole("listitem")).toHaveCount(files.length, {
    timeout: UPLOAD_TIMEOUT_MS,
  });
  await expect(input).toBeEnabled();
}

/** Upload `files` on the current /fira page in batches of MAX_FILES_PER_PICK, one after another. */
export async function uploadAll(page: Page, files: string[]): Promise<void> {
  const batches = Array.from({ length: Math.ceil(files.length / MAX_FILES_PER_PICK) }, (_, i) =>
    files.slice(i * MAX_FILES_PER_PICK, (i + 1) * MAX_FILES_PER_PICK),
  );
  // Each batch waits for the previous one's results before it is picked.
  await batches.reduce(async (previous, batch) => {
    await previous;
    await uploadBatch(page, batch);
  }, Promise.resolve());
}

/** Generate the samples, open /fira and upload all of them (19 match, 2 need review). */
export async function uploadSampleFiras(page: Page): Promise<void> {
  const files = samplePdfs();
  await page.goto("/fira");
  await uploadAll(page, files);
  await expect(page.getByRole("group", { name: "Matched", exact: true })).toContainText("19");
}
