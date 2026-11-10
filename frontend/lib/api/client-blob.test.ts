import { http, HttpResponse } from "msw";

import { server } from "@/test/msw/server";

import { ApiError, apiGetBlob, fileNameFromDisposition } from "./client";

const API = "http://api.test";

async function caught(promise: Promise<unknown>): Promise<ApiError> {
  try {
    await promise;
  } catch (error) {
    if (error instanceof ApiError) return error;
  }
  throw new Error("expected ApiError");
}

describe("apiGetBlob", () => {
  it("returns the body and the Content-Disposition file name", async () => {
    server.use(
      http.get(
        `${API}/file`,
        () =>
          new HttpResponse("%PDF-1.7", {
            headers: { "Content-Disposition": 'attachment; filename="a-b.pdf"' },
          }),
      ),
    );
    const { blob, fileName } = await apiGetBlob("/file");
    expect(fileName).toBe("a-b.pdf");
    expect(await blob.text()).toBe("%PDF-1.7");
  });

  it("falls back to the given name, then the constant", async () => {
    server.use(http.get(`${API}/file`, () => new HttpResponse("x")));
    expect((await apiGetBlob("/file", { fallbackName: "x.pdf" })).fileName).toBe("x.pdf");
    expect((await apiGetBlob("/file")).fileName).toBe("paylens-ca-report.pdf");
  });

  it("maps the standard error body", async () => {
    server.use(
      http.get(`${API}/file`, () =>
        HttpResponse.json(
          { error: { code: "VALIDATION_ERROR", message: "Unknown period." } },
          { status: 422 },
        ),
      ),
    );
    const error = await caught(apiGetBlob("/file"));
    expect([error.status, error.code, error.message]).toEqual([
      422,
      "VALIDATION_ERROR",
      "Unknown period.",
    ]);
  });

  it("maps network failures and timeouts", async () => {
    server.use(http.get(`${API}/down`, () => HttpResponse.error()));
    expect((await caught(apiGetBlob("/down"))).code).toBe("NETWORK_ERROR");
    server.use(
      http.get(`${API}/slow`, async () => {
        await new Promise((resolve) => setTimeout(resolve, 200));
        return new HttpResponse("late");
      }),
    );
    expect((await caught(apiGetBlob("/slow", { timeoutMs: 20 }))).code).toBe("TIMEOUT");
  });
});

describe("fileNameFromDisposition", () => {
  it.each([
    ['attachment; filename="r.pdf"', "r.pdf"],
    ["attachment; filename=r.pdf", "r.pdf"],
    ["attachment; filename*=UTF-8''r%20x.pdf", "r x.pdf"],
    ["attachment", null],
    [null, null],
  ])("parses %s", (header, expected) => {
    expect(fileNameFromDisposition(header)).toBe(expected);
  });
});
