import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { delay, http, HttpResponse } from "msw";

import { wakeDefaults } from "@/lib/api/wake";
import { WAKE_MESSAGES } from "@/lib/constants";
import { server } from "@/test/msw/server";

import { WakeNotice } from "./WakeNotice";

const API = "http://api.test";
const { NOTICE_DELAY_MS } = vi.hoisted(() => ({ NOTICE_DELAY_MS: 20 }));
const SLOW_START_MS = 200;
const RETRY_WINDOW_MS = 1_500;
const SERVICE_UNAVAILABLE = 503;
const WAIT_FACTOR = 2; // wait twice as long as the thing being waited for
const CALLS_WITH_ONE_RETRY = 2;

vi.mock("@/lib/constants", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/lib/constants")>()),
  WAKE_NOTICE_DELAY_MS: NOTICE_DELAY_MS,
}));

afterEach(() => {
  wakeDefaults.windowMs = 0;
});

describe("WakeNotice", () => {
  it("shows nothing when the backend answers at once", async () => {
    server.use(http.get(`${API}/health`, () => HttpResponse.json({ status: "ok" })));
    const { container } = render(<WakeNotice />);
    await delay(NOTICE_DELAY_MS * WAIT_FACTOR);
    expect(container).toBeEmptyDOMElement();
  });

  it("shows the waking notice while the backend starts, then hides it", async () => {
    server.use(
      http.get(`${API}/health`, async () => {
        await delay(SLOW_START_MS);
        return HttpResponse.json({ status: "ok" });
      }),
    );
    render(<WakeNotice />);
    expect(await screen.findByText(WAKE_MESSAGES.waking)).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.queryByText(WAKE_MESSAGES.waking)).not.toBeInTheDocument();
    });
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("keeps waiting through 503 answers from the proxy", async () => {
    wakeDefaults.windowMs = RETRY_WINDOW_MS;
    let calls = 0;
    server.use(
      http.get(`${API}/health`, () => {
        calls += 1;
        return calls === 1
          ? HttpResponse.json({}, { status: SERVICE_UNAVAILABLE })
          : HttpResponse.json({ status: "ok" });
      }),
    );
    render(<WakeNotice />);
    expect(await screen.findByText(WAKE_MESSAGES.waking)).toBeInTheDocument();
    await waitFor(
      () => {
        expect(screen.queryByText(WAKE_MESSAGES.waking)).not.toBeInTheDocument();
      },
      { timeout: RETRY_WINDOW_MS * WAIT_FACTOR },
    );
    expect(calls).toBe(CALLS_WITH_ONE_RETRY);
  });

  it("offers a retry when the backend never starts", async () => {
    let up = false;
    server.use(
      http.get(`${API}/health`, () =>
        up ? HttpResponse.json({ status: "ok" }) : HttpResponse.error(),
      ),
    );
    render(<WakeNotice />);
    expect(await screen.findByText(WAKE_MESSAGES.down)).toBeInTheDocument();
    up = true;
    await userEvent.click(screen.getByRole("button", { name: "Try again" }));
    await waitFor(() => {
      expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    });
  });
});
