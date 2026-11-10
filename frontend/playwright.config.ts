import { defineConfig, devices } from "@playwright/test";

const API_PORT = 8001;
const WEB_PORT = 3001;
const E2E_DATABASE_URL = process.env.E2E_DATABASE_URL ?? "postgresql+psycopg:///paylens_e2e";
const SERVER_TIMEOUT_MS = 120_000;

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  forbidOnly: Boolean(process.env.CI),
  retries: 0,
  reporter: process.env.CI ? "github" : "list",
  globalSetup: "./e2e/global-setup.ts",
  use: { baseURL: `http://localhost:${WEB_PORT}`, trace: "retain-on-failure" },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
    {
      name: "mobile",
      use: { ...devices["Desktop Chrome"], viewport: { width: 390, height: 844 } },
    },
  ],
  webServer: [
    {
      command: `uv run --directory ../backend uvicorn app.main:app --port ${API_PORT}`,
      url: `http://localhost:${API_PORT}/health`,
      env: {
        APP_ENV: "test",
        PAYPAL_MODE: "fake",
        STARTUP_SYNC_ENABLED: "false",
        RATE_LIMIT_ENABLED: "false",
        DATABASE_URL: E2E_DATABASE_URL,
        FRONTEND_URL: `http://localhost:${WEB_PORT}`,
      },
      reuseExistingServer: false,
      timeout: SERVER_TIMEOUT_MS,
    },
    {
      command: `npm run build && npx next start --port ${WEB_PORT}`,
      port: WEB_PORT,
      env: {
        NEXT_PUBLIC_API_URL: `http://localhost:${API_PORT}`,
        NEXT_PUBLIC_PAYPAL_MODE: "fake",
        NEXT_PUBLIC_PAYPAL_CLIENT_ID: "test",
      },
      reuseExistingServer: false,
      timeout: SERVER_TIMEOUT_MS,
    },
  ],
});
