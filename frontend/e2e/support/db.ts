import { execFileSync } from "node:child_process";

export const API_URL = "http://localhost:8001";
const E2E_DATABASE_URL = process.env.E2E_DATABASE_URL ?? "postgresql+psycopg:///paylens_e2e";

function runBackendScript(...args: string[]): void {
  execFileSync("uv", ["run", "--directory", "../backend", "python", "-m", ...args], {
    env: {
      ...process.env,
      APP_ENV: "test",
      PAYPAL_MODE: "fake",
      FX_MODE: "fake",
      LLM_MODE: "fake",
      DATABASE_URL: E2E_DATABASE_URL,
    },
    stdio: "ignore",
  });
}

/** Drop and recreate the e2e database so each test starts from the same empty state. */
export function resetDatabase(): void {
  runBackendScript("scripts.reset_db");
}

/** Load the 24 "Demo seed" rows (FR-040). */
export function seedDemo(): void {
  runBackendScript("scripts.seed_demo");
}

/** Write the demo FIRA PDFs (research R4: 21 files for SEED-0001…0021) into `outDir`. */
export function generateFiraSamples(outDir: string): void {
  runBackendScript("scripts.generate_fira_samples", "--out", outDir);
}

/** The app's ₹ display format (en-IN), for comparing API amounts with the screen. */
export function formatInr(amount: string): string {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" }).format(
    amount as Intl.StringNumericLiteral,
  );
}

/**
 * How an INR amount appears in the raw CA report PDF: "₹" comes from the embedded rupee font, then
 * the en-IN grouped digits are their own string, e.g. "(1,23,456.78)".
 */
export function formatReportInr(amount: string): string {
  const grouped = new Intl.NumberFormat("en-IN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount as Intl.StringNumericLiteral);
  // The PDF draws "₹" with the embedded rupee font, then the digits as their own text string.
  return `(${grouped})`;
}

/** Undo PDF string escaping of "(" and ")" so report text can be searched as written. */
export function pdfText(raw: string): string {
  return raw.replaceAll("\\(", "(").replaceAll("\\)", ")");
}
