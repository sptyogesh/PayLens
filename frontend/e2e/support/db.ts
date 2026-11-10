import { execFileSync } from "node:child_process";

export const API_URL = "http://localhost:8001";
const E2E_DATABASE_URL = process.env.E2E_DATABASE_URL ?? "postgresql+psycopg:///paylens_e2e";

/** Drop and recreate the e2e database so each test starts from the same empty state. */
export function resetDatabase(): void {
  execFileSync("uv", ["run", "--directory", "../backend", "python", "-m", "scripts.reset_db"], {
    env: { ...process.env, APP_ENV: "test", PAYPAL_MODE: "fake", DATABASE_URL: E2E_DATABASE_URL },
    stdio: "ignore",
  });
}
