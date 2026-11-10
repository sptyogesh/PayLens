// ESLint flat config. Size limits enforce constitution Principle XIII.
import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";
import tseslint from "typescript-eslint";
import { importX } from "eslint-plugin-import-x";

const FILE_MAX_LINES = 200;
const COMPONENT_MAX_LINES = 150;
const TEST_MAX_LINES = 300;
const FUNCTION_MAX_LINES = 40;
const maxLines = (max) => ["error", { max }];

export default defineConfig([
  ...nextVitals,
  ...nextTs,
  ...tseslint.configs.strictTypeChecked,
  {
    languageOptions: {
      parserOptions: { projectService: true, tsconfigRootDir: import.meta.dirname },
    },
    plugins: { "import-x": importX },
    rules: {
      "@typescript-eslint/no-explicit-any": "error",
      "@typescript-eslint/restrict-template-expressions": ["error", { allowNumber: true }],
      "import-x/no-cycle": "error",
      "max-lines": maxLines(FILE_MAX_LINES),
      "max-lines-per-function": ["error", { max: FUNCTION_MAX_LINES, IIFEs: true }],
    },
  },
  { files: ["**/*.tsx"], rules: { "max-lines": maxLines(COMPONENT_MAX_LINES) } },
  {
    files: ["**/*.test.ts", "**/*.test.tsx", "e2e/**/*.ts", "test/**/*.ts"],
    rules: { "max-lines": maxLines(TEST_MAX_LINES), "max-lines-per-function": "off" },
  },
  {
    files: ["*.config.mjs", "*.config.ts", "*.mjs"],
    ...tseslint.configs.disableTypeChecked,
  },
  globalIgnores([
    "**/.next/**",
    "out/**",
    "build/**",
    "coverage/**",
    "playwright-report/**",
    "test-results/**",
    "next-env.d.ts",
    "lib/api/api-types.ts",
  ]),
]);
