import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";

import { downloadBlob } from "@/lib/download";
import { API, REPORT_PDF_BYTES } from "@/test/msw/handlers";
import { server } from "@/test/msw/server";

import { DashboardView } from "../DashboardView";
import { DownloadReportButton } from "./DownloadReportButton";

vi.mock("@/lib/download", () => ({ downloadBlob: vi.fn() }));
const downloadMock = vi.mocked(downloadBlob);

const DOWNLOAD = { name: "Download CA report" } as const;

function rateLimited() {
  return HttpResponse.json(
    { error: { code: "RATE_LIMITED", message: "Too many requests. Try again in a minute." } },
    { status: 429 },
  );
}

describe("DownloadReportButton", () => {
  beforeEach(() => {
    downloadMock.mockReset();
  });

  it("requests the current period and downloads the blob with the server file name", async () => {
    const periods: (string | null)[] = [];
    server.use(
      http.get(`${API}/report.pdf`, ({ request }) => {
        periods.push(new URL(request.url).searchParams.get("period"));
        return new HttpResponse(REPORT_PDF_BYTES, {
          headers: {
            "Content-Type": "application/pdf",
            "Content-Disposition":
              'attachment; filename="paylens-ca-report-all_time-2026-11-10.pdf"',
          },
        });
      }),
    );
    render(<DownloadReportButton period="all_time" />);
    await userEvent.click(screen.getByRole("button", DOWNLOAD));
    await vi.waitFor(() => {
      expect(downloadMock).toHaveBeenCalledOnce();
    });
    expect(periods).toEqual(["all_time"]);
    const [blob, fileName] = downloadMock.mock.calls[0] ?? [];
    expect(fileName).toBe("paylens-ca-report-all_time-2026-11-10.pdf");
    expect(await blob?.text()).toBe(REPORT_PDF_BYTES);
    expect(screen.getByRole("button", DOWNLOAD)).toBeEnabled();
  });

  it("uses the dashboard's newly chosen period", async () => {
    const periods: (string | null)[] = [];
    server.use(
      http.get(`${API}/report.pdf`, ({ request }) => {
        periods.push(new URL(request.url).searchParams.get("period"));
        return new HttpResponse(REPORT_PDF_BYTES, {
          headers: { "Content-Type": "application/pdf" },
        });
      }),
    );
    render(<DashboardView />);
    await userEvent.click(screen.getByRole("button", DOWNLOAD));
    await vi.waitFor(() => {
      expect(downloadMock).toHaveBeenCalledTimes(1);
    });
    await userEvent.click(screen.getByRole("radio", { name: "This month" }));
    await userEvent.click(screen.getByRole("button", DOWNLOAD));
    await vi.waitFor(() => {
      expect(downloadMock).toHaveBeenCalledTimes(2);
    });
    expect(periods).toEqual(["last_3_months", "this_month"]);
    expect(downloadMock.mock.calls[1]?.[1]).toBe("paylens-ca-report.pdf");
  });

  it.each([
    [429, "Too many requests. Try again in a minute.", rateLimited],
    [500, "Something went wrong. Please try again.", () => new HttpResponse(null, { status: 500 })],
  ])("shows the %i error and retries", async (_status, message, failure) => {
    let fail = true;
    server.use(
      http.get(`${API}/report.pdf`, () =>
        fail ? failure() : new HttpResponse(REPORT_PDF_BYTES, { status: 200 }),
      ),
    );
    render(<DownloadReportButton period="last_3_months" />);
    await userEvent.click(screen.getByRole("button", DOWNLOAD));
    expect(await screen.findByRole("alert")).toHaveTextContent(message);
    expect(downloadMock).not.toHaveBeenCalled();
    fail = false;
    await userEvent.click(screen.getByRole("button", { name: "Try again" }));
    await vi.waitFor(() => {
      expect(downloadMock).toHaveBeenCalledOnce();
    });
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("shows the pending label and disables the button while the report is prepared", async () => {
    let release: () => void = () => undefined;
    const gate = new Promise<void>((resolve) => {
      release = resolve;
    });
    server.use(
      http.get(`${API}/report.pdf`, async () => {
        await gate;
        return new HttpResponse(REPORT_PDF_BYTES, { status: 200 });
      }),
    );
    render(<DownloadReportButton period="last_3_months" />);
    await userEvent.click(screen.getByRole("button", DOWNLOAD));
    const pending = await screen.findByRole("button", { name: "Preparing report…" });
    expect(pending).toBeDisabled();
    release();
    expect(await screen.findByRole("button", DOWNLOAD)).toBeEnabled();
    expect(downloadMock).toHaveBeenCalledOnce();
  });
});
