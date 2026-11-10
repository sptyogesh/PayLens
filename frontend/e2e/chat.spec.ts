import AxeBuilder from "@axe-core/playwright";
import type { Locator, Page } from "@playwright/test";
import { expect, test } from "@playwright/test";

import { API_URL, formatInr as inr, resetDatabase, seedDemo } from "./support/db";
import { uploadSampleFiras } from "./support/fira";

const BLOCKING_IMPACTS = new Set(["critical", "serious"]);
const NOT_TAX_ADVICE = "Prepared from user data — not tax advice. Confirm with a CA.";
/** The backend's fake LLM raises (AI down) for any question containing this marker. */
const FAKE_FAIL = "FAKE_FAIL";
const FIRA_CHAT_TIMEOUT_MS = 180_000;

type FiraList = { missing: { date: string; client: string }[] };

test.beforeEach(() => {
  resetDatabase();
  seedDemo();
});

/** Type a question, send it, and return the new answer bubble. */
async function ask(page: Page, question: string): Promise<Locator> {
  const answers = page.getByRole("article", { name: "PayLens assistant" });
  const before = await answers.count();
  await page.getByLabel("Your question").fill(question);
  await page.getByRole("button", { name: "Send" }).click();
  await expect(answers).toHaveCount(before + 1);
  return answers.nth(before);
}

test("E5 the FX loss answer matches the dashboard API for all time", async ({ page, request }) => {
  const api = (await (await request.get(`${API_URL}/dashboard?period=all_time`)).json()) as {
    totals: { fx_loss_inr: { amount: string } };
  };
  const amount = inr(api.totals.fx_loss_inr.amount);

  await page.goto("/chat");
  const answer = await ask(page, "How much FX loss in all time?");
  await expect(answer.getByText(amount).first()).toBeVisible();
  const figures = answer.getByRole("list", { name: "Based on" });
  await expect(figures.getByRole("listitem").filter({ hasText: "FX loss" })).toContainText(amount);
});

test("E6 a question with no data says it is not available and shows no ₹ figure", async ({
  page,
}) => {
  await page.goto("/chat");
  const answer = await ask(page, "How much income did I get in December 2030?");
  await expect(answer).toContainText("not available");
  await expect(answer).not.toContainText("₹");
  await expect(answer.getByRole("list", { name: "Based on" })).toHaveCount(0);
});

test("a tax question carries the CA disclaimer", async ({ page }) => {
  await page.goto("/chat");
  const answer = await ask(page, "How much tax should I pay this financial year?");
  await expect(answer.getByRole("note")).toHaveText(NOT_TAX_ADVICE);
});

test("E11 no horizontal scroll and E12 no blocking a11y violations on /chat", async ({ page }) => {
  await page.goto("/chat");
  await expect(page.getByRole("heading", { name: "Ask your money" })).toBeVisible();
  await page.getByRole("button", { name: "How much FX loss last quarter?" }).click();
  await expect(page.getByRole("article", { name: "PayLens assistant" })).toHaveCount(1);
  await expect(page.getByLabel("Your question")).toBeEditable();
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  expect(overflow).toBeLessThanOrEqual(0);
  const results = await new AxeBuilder({ page }).analyze();
  const blocking = results.violations.filter((v) => BLOCKING_IMPACTS.has(v.impact ?? ""));
  expect(blocking.map((v) => `${v.id}: ${v.help}`)).toEqual([]);
});

test("FR-002 no LLM key or provider URL reaches the browser", async ({ page, request }) => {
  const scripts: string[] = [];
  page.on("response", (response) => {
    if (response.url().endsWith(".js")) scripts.push(response.url());
  });
  await page.goto("/chat");
  await expect(page.getByRole("heading", { name: "Ask your money" })).toBeVisible();
  expect(scripts.length).toBeGreaterThan(0);
  for (const url of scripts) {
    const body = await (await request.get(url)).text();
    expect(body).not.toContain("api.anthropic.com");
    expect(body).not.toContain("LLM_API_KEY");
    expect(body).not.toContain("x-api-key");
  }
});

test("003 US3 the chat stays usable when the AI fails: fallback answer, then a normal answer", async ({
  page,
}) => {
  await page.goto("/chat");
  const fallback = await ask(page, `${FAKE_FAIL} how much income?`);
  await expect(fallback).toContainText("The assistant is not available right now");
  await expect(fallback).toContainText("could not give a full answer");
  // No error state: the question counts as answered (Next.js keeps an empty route-announcer alert).
  await expect(page.getByText("Not answered")).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Try again" })).toHaveCount(0);
  await expect(page.getByRole("heading", { name: "Ask your money" })).toBeVisible();

  const next = await ask(page, "How much FX loss in all time?");
  await expect(next).not.toContainText("could not give a full answer");
  await expect(next.getByRole("list", { name: "Based on" })).toBeVisible();
});

test("004 US3 the chat lists the payments missing a FIRA after the samples are uploaded", async ({
  page,
}) => {
  test.setTimeout(FIRA_CHAT_TIMEOUT_MS);
  await uploadSampleFiras(page);
  const fira = (await (await page.request.get(`${API_URL}/fira`)).json()) as FiraList;
  expect(fira.missing).toHaveLength(3);

  await page.goto("/chat");
  const answer = await ask(page, "Which payments are missing a FIRA?");
  for (const payment of fira.missing) {
    await expect(answer).toContainText(`${payment.date} ${payment.client}`);
  }
  const figures = answer.getByRole("list", { name: "Based on" });
  await expect(figures.getByRole("listitem").filter({ hasText: "Missing:" })).toContainText(
    "Missing: 3",
  );
});
