import { execFileSync } from "node:child_process";

/** Reset the e2e database before the run so every run starts from the same state. */
export default function globalSetup(): void {
  const databaseUrl = process.env.E2E_DATABASE_URL ?? "postgresql+psycopg:///paylens_e2e";
  execFileSync("uv", ["run", "--directory", "../backend", "python", "-m", "scripts.reset_db"], {
    env: { ...process.env, APP_ENV: "test", PAYPAL_MODE: "fake", DATABASE_URL: databaseUrl },
    stdio: "inherit",
  });
}
