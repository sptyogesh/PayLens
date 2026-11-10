import { act, renderHook, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { z } from "zod";

import { server } from "@/test/msw/server";

import { useApi } from "./useApi";

const API = "http://api.test";
const Schema = z.object({ total: z.string() });

describe("useApi (U8)", () => {
  it("goes loading → success", async () => {
    server.use(http.get(`${API}/x`, () => HttpResponse.json({ total: "1.00" })));
    const { result } = renderHook(() => useApi("/x", Schema));
    expect(result.current.status).toBe("loading");
    await waitFor(() => {
      expect(result.current).toMatchObject({ status: "success", data: { total: "1.00" } });
    });
  });

  it("goes loading → error on HTTP error", async () => {
    server.use(http.get(`${API}/x`, () => HttpResponse.json({}, { status: 500 })));
    const { result } = renderHook(() => useApi("/x", Schema));
    await waitFor(() => {
      expect(result.current.status).toBe("error");
    });
  });

  it("reports invalid data as an error", async () => {
    server.use(http.get(`${API}/x`, () => HttpResponse.json({ total: 1 })));
    const { result } = renderHook(() => useApi("/x", Schema));
    await waitFor(() => {
      expect(result.current).toMatchObject({
        status: "error",
        error: { code: "INVALID_RESPONSE" },
      });
    });
  });

  it("reload fetches again", async () => {
    let calls = 0;
    server.use(
      http.get(`${API}/x`, () => {
        calls += 1;
        return HttpResponse.json({ total: `${calls}.00` });
      }),
    );
    const { result } = renderHook(() => useApi("/x", Schema));
    await waitFor(() => {
      expect(result.current.status).toBe("success");
    });
    act(() => {
      result.current.reload();
    });
    await waitFor(() => {
      expect(result.current).toMatchObject({ data: { total: "2.00" } });
    });
  });
});

describe("useApi path changes", () => {
  it("shows loading for a new path instead of the previous path's data", async () => {
    server.use(
      http.get(`${API}/a`, () => HttpResponse.json({ total: "1.00" })),
      http.get(`${API}/b`, async () => {
        await new Promise((resolve) => setTimeout(resolve, 50));
        return HttpResponse.json({ total: "2.00" });
      }),
    );
    const { result, rerender } = renderHook(({ path }) => useApi(path, Schema), {
      initialProps: { path: "/a" },
    });
    await waitFor(() => {
      expect(result.current).toMatchObject({ status: "success", data: { total: "1.00" } });
    });
    rerender({ path: "/b" });
    expect(result.current.status).toBe("loading");
    await waitFor(() => {
      expect(result.current).toMatchObject({ status: "success", data: { total: "2.00" } });
    });
  });
});
