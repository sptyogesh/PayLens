import { act, renderHook } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { z } from "zod";

import { server } from "@/test/msw/server";

import { useMutation } from "./useMutation";

const API = "http://api.test";
const Schema = z.object({ id: z.string() });

describe("useMutation", () => {
  it("runs and stores the data", async () => {
    server.use(http.post(`${API}/y`, () => HttpResponse.json({ id: "a" })));
    const { result } = renderHook(() => useMutation("/y", Schema));
    expect(result.current.state.status).toBe("idle");
    let returned: unknown;
    await act(async () => {
      returned = await result.current.run({ x: 1 });
    });
    expect(returned).toEqual({ id: "a" });
    expect(result.current.state).toEqual({ status: "success", data: { id: "a" } });
  });

  it("stores the error and returns null", async () => {
    server.use(
      http.post(`${API}/y`, () =>
        HttpResponse.json(
          { error: { code: "RATE_LIMITED", message: "Slow down" } },
          { status: 429 },
        ),
      ),
    );
    const { result } = renderHook(() => useMutation("/y", Schema));
    let returned: unknown = "unset";
    await act(async () => {
      returned = await result.current.run();
    });
    expect(returned).toBeNull();
    expect(result.current.state).toMatchObject({
      status: "error",
      error: { code: "RATE_LIMITED" },
    });
  });
});
