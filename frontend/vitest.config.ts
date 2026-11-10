import react from "@vitejs/plugin-react";
import { fileURLToPath } from "node:url";
import { defineConfig } from "vitest/config";

const COVERAGE_TARGET = 80;

export default defineConfig({
  plugins: [react()],
  resolve: { alias: { "@": fileURLToPath(new URL("./", import.meta.url)) } },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./test/setup.ts"],
    include: ["**/*.test.{ts,tsx}"],
    exclude: ["node_modules/**", "e2e/**", ".next/**"],
    env: { NEXT_PUBLIC_API_URL: "http://api.test", NEXT_PUBLIC_PAYPAL_MODE: "fake" },
    coverage: {
      provider: "v8",
      include: ["components/ui/**", "lib/**"],
      exclude: ["**/*.test.*", "**/index.ts", "lib/api/api-types.ts", "lib/api/openapi.json"],
      thresholds: {
        lines: COVERAGE_TARGET,
        functions: COVERAGE_TARGET,
        branches: COVERAGE_TARGET,
        statements: COVERAGE_TARGET,
      },
    },
  },
});
