/**
 * Build guard (runs as `prebuild`): NEXT_PUBLIC_* values are baked into the bundle by `next build`,
 * so a missing or wrong value would ship a frontend that cannot reach the backend. Fails the build
 * with a clear message instead. Self-contained (Node runs this file directly; no path aliases).
 */
import { fileURLToPath } from "node:url";

export type PublicEnv = Readonly<Record<string, string | undefined>>;

const PAYPAL_MODES: readonly string[] = ["http", "fake"];
const LOCAL_HOSTS: readonly string[] = ["localhost", "127.0.0.1"];
const WEB_PROTOCOLS: readonly string[] = ["http:", "https:"];

function apiUrlProblems(raw: string | undefined, realMode: boolean): string[] {
  if (!raw)
    return [
      "NEXT_PUBLIC_API_URL is not set (the backend URL, e.g. https://paylens-api.onrender.com).",
    ];
  let url: URL;
  try {
    url = new URL(raw);
  } catch {
    return ["NEXT_PUBLIC_API_URL is not a full URL (it must start with https://)."];
  }
  const problems: string[] = [];
  if (!WEB_PROTOCOLS.includes(url.protocol)) problems.push("NEXT_PUBLIC_API_URL must be http(s).");
  if (realMode && url.protocol !== "https:" && !LOCAL_HOSTS.includes(url.hostname)) {
    problems.push("NEXT_PUBLIC_API_URL must use https:// outside localhost.");
  }
  if (raw.endsWith("/")) problems.push("NEXT_PUBLIC_API_URL must not end with '/'.");
  return problems;
}

/** Every problem with the public build variables; empty when the build may go on. */
export function publicEnvProblems(env: PublicEnv): readonly string[] {
  const mode = env.NEXT_PUBLIC_PAYPAL_MODE ?? "";
  const problems: string[] = [];
  if (!PAYPAL_MODES.includes(mode)) {
    problems.push("NEXT_PUBLIC_PAYPAL_MODE must be http (real sandbox) or fake (tests).");
  }
  problems.push(...apiUrlProblems(env.NEXT_PUBLIC_API_URL, mode === "http"));
  if (mode === "http" && !env.NEXT_PUBLIC_PAYPAL_CLIENT_ID) {
    problems.push("NEXT_PUBLIC_PAYPAL_CLIENT_ID is not set (the PayPal sandbox client ID).");
  }
  return problems;
}

function main(): void {
  const problems = publicEnvProblems(process.env);
  if (problems.length === 0) return;
  console.error("Build stopped: NEXT_PUBLIC_* values are baked in at build time.");
  console.error(problems.map((problem) => `- ${problem}`).join("\n"));
  console.error("Set them (Render: paylens-web → Environment), then deploy again.");
  process.exit(1);
}

if (process.argv[1] === fileURLToPath(import.meta.url)) main();
