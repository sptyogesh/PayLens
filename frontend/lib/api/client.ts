/** Typed fetch for the PayLens API: errors use one shape, responses are zod-validated. */
import type { z } from "zod";

import { MESSAGES } from "../constants";
import { ApiErrorBodySchema, parseWith } from "./schemas";

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function apiUrl(path: string): string {
  return `${process.env.NEXT_PUBLIC_API_URL ?? ""}${path}`;
}

async function readJson(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) return null;
  try {
    return JSON.parse(text) as unknown;
  } catch {
    return undefined;
  }
}

async function send<T>(path: string, schema: z.ZodType<T>, init: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(apiUrl(path), init);
  } catch {
    throw new ApiError(0, "NETWORK_ERROR", MESSAGES.networkError);
  }
  const body = await readJson(response);
  if (!response.ok) {
    const parsed = parseWith(ApiErrorBodySchema, body);
    const message = parsed?.error.message ?? MESSAGES.genericError;
    throw new ApiError(response.status, parsed?.error.code ?? "HTTP_ERROR", message);
  }
  const data = parseWith(schema, body);
  if (data === null)
    throw new ApiError(response.status, "INVALID_RESPONSE", MESSAGES.invalidResponse);
  return data;
}

export function apiGet<T>(path: string, schema: z.ZodType<T>): Promise<T> {
  return send(path, schema, { method: "GET" });
}

export function apiPost<T>(path: string, body: unknown, schema: z.ZodType<T>): Promise<T> {
  return send(path, schema, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body ?? {}),
  });
}
