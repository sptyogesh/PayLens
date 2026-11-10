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

/** The app's ₹ display format (en-IN), for comparing API amounts with the screen. */
export function formatInr(amount: string): string {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" }).format(
    amount as Intl.StringNumericLiteral,
  );
}
