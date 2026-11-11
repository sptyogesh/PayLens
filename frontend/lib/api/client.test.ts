import { http, HttpResponse } from "msw";
import { z } from "zod";

import { server } from "@/test/msw/server";

import { ApiError, apiGet, apiPost, apiPostBytes } from "./client";
import { MoneySchema } from "./schemas";

const API = "http://api.test";
const PriceSchema = z.object({ price: MoneySchema });

async function caught(promise: Promise<unknown>): Promise<ApiError> {
  try {
    await promise;
  } catch (error) {
    if (error instanceof ApiError) return error;
  }
  throw new Error("expected ApiError");
}

describe("api client", () => {
  it("returns validated data", async () => {
    server.use(
      http.get(`${API}/price`, () =>
        HttpResponse.json({ price: { amount: "10.00", currency: "USD" } }),
      ),
    );
    await expect(apiGet("/price", PriceSchema)).resolves.toEqual({
      price: { amount: "10.00", currency: "USD" },
    });
  });

  it("U3 rejects a numeric money field", async () => {
    server.use(
      http.get(`${API}/price`, () => HttpResponse.json({ price: { amount: 10, currency: "USD" } })),
    );
    const error = await caught(apiGet("/price", PriceSchema));
    expect(error.code).toBe("INVALID_RESPONSE");
  });

  it("maps the standard error shape", async () => {
    server.use(
      http.post(`${API}/sync`, () =>
        HttpResponse.json(
          { error: { code: "SYNC_IN_PROGRESS", message: "A sync is already running." } },
          { status: 409 },
        ),
      ),
    );
    const error = await caught(apiPost("/sync", {}, PriceSchema));
    expect([error.status, error.code, error.message]).toEqual([
      409,
      "SYNC_IN_PROGRESS",
      "A sync is already running.",
    ]);
  });

  it("maps a non-JSON error to a generic message", async () => {
    server.use(http.get(`${API}/price`, () => new HttpResponse("oops", { status: 500 })));
    const error = await caught(apiGet("/price", PriceSchema));
    expect([error.status, error.code]).toEqual([500, "HTTP_ERROR"]);
  });

  it("maps a network failure", async () => {
    server.use(http.get(`${API}/price`, () => HttpResponse.error()));
    const error = await caught(apiGet("/price", PriceSchema));
    expect(error.code).toBe("NETWORK_ERROR");
  });

  it("aborts a POST that takes longer than its timeout", async () => {
    server.use(
      http.post(`${API}/slow`, async () => {
        await new Promise((resolve) => setTimeout(resolve, 200));
        return HttpResponse.json({ total: "1.00" });
      }),
    );
    const error = await caught(apiPost("/slow", {}, PriceSchema, { timeoutMs: 20 }));
    expect([error.status, error.code]).toEqual([0, "TIMEOUT"]);
  });

  it("posts raw bytes with their content type", async () => {
    let seen: { type: string | null; body: string } | null = null;
    server.use(
      http.post(`${API}/upload`, async ({ request }) => {
        seen = { type: request.headers.get("content-type"), body: await request.text() };
        return HttpResponse.json({ price: { amount: "1.00", currency: "USD" } });
      }),
    );
    const blob = new Blob(["%PDF-1.4"], { type: "application/pdf" });
    await expect(apiPostBytes("/upload", blob, "application/pdf", PriceSchema)).resolves.toEqual({
      price: { amount: "1.00", currency: "USD" },
    });
    expect(seen).toEqual({ type: "application/pdf", body: "%PDF-1.4" });
  });
});
