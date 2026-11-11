/** Typed fetch for the PayLens API: errors use one shape, responses are zod-validated. */
import type { z } from "zod";

import { DOWNLOAD_FALLBACK_FILE_NAME, MESSAGES } from "../constants";
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

/** fetch with the shared error handling: network/timeout and non-OK become ApiError. */
async function fetchOk(path: string, init: RequestInit): Promise<Response> {
  let response: Response;
  try {
    response = await fetch(apiUrl(path), init);
  } catch {
    if (init.signal?.aborted) throw new ApiError(0, "TIMEOUT", MESSAGES.timeout);
    throw new ApiError(0, "NETWORK_ERROR", MESSAGES.networkError);
  }
  if (!response.ok) {
    const parsed = parseWith(ApiErrorBodySchema, await readJson(response));
    const message = parsed?.error.message ?? MESSAGES.genericError;
    throw new ApiError(response.status, parsed?.error.code ?? "HTTP_ERROR", message);
  }
  return response;
}

async function send<T>(path: string, schema: z.ZodType<T>, init: RequestInit): Promise<T> {
  const response = await fetchOk(path, init);
  const data = parseWith(schema, await readJson(response));
  if (data === null)
    throw new ApiError(response.status, "INVALID_RESPONSE", MESSAGES.invalidResponse);
  return data;
}

export function apiGet<T>(path: string, schema: z.ZodType<T>): Promise<T> {
  return send(path, schema, { method: "GET" });
}

export type PostOptions = { timeoutMs?: number };

/** POST JSON. `timeoutMs` aborts a request that hangs (e.g. a slow AI answer). */
export function apiPost<T>(
  path: string,
  body: unknown,
  schema: z.ZodType<T>,
  options: PostOptions = {},
): Promise<T> {
  return send(path, schema, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body ?? {}),
    ...(options.timeoutMs ? { signal: AbortSignal.timeout(options.timeoutMs) } : {}),
  });
}

/** POST raw bytes (e.g. one PDF) with its content type; the response is zod-validated. */
export function apiPostBytes<T>(
  path: string,
  body: Blob,
  contentType: string,
  schema: z.ZodType<T>,
  options: PostOptions = {},
): Promise<T> {
  return send(path, schema, {
    method: "POST",
    headers: { "Content-Type": contentType },
    body,
    ...(options.timeoutMs ? { signal: AbortSignal.timeout(options.timeoutMs) } : {}),
  });
}

export type BlobResult = { blob: Blob; fileName: string };

/** The `filename` from a Content-Disposition header, or null when absent. */
export function fileNameFromDisposition(header: string | null): string | null {
  const match = /filename\*?=(?:UTF-8'')?"?([^";]+)"?/i.exec(header ?? "");
  const raw = match?.[1];
  if (!raw) return null;
  try {
    return decodeURIComponent(raw.trim());
  } catch {
    return raw.trim();
  }
}

export type BlobOptions = PostOptions & { fallbackName?: string };

/** GET a file (e.g. a PDF). The name comes from Content-Disposition, else `fallbackName`. */
export async function apiGetBlob(path: string, options: BlobOptions = {}): Promise<BlobResult> {
  const response = await fetchOk(path, {
    method: "GET",
    ...(options.timeoutMs ? { signal: AbortSignal.timeout(options.timeoutMs) } : {}),
  });
  try {
    const blob = await response.blob();
    const fileName = fileNameFromDisposition(response.headers.get("Content-Disposition"));
    return { blob, fileName: fileName ?? options.fallbackName ?? DOWNLOAD_FALLBACK_FILE_NAME };
  } catch {
    if (options.timeoutMs) throw new ApiError(0, "TIMEOUT", MESSAGES.timeout);
    throw new ApiError(0, "NETWORK_ERROR", MESSAGES.networkError);
  }
}
