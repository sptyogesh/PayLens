import { render, screen } from "@testing-library/react";

import { ApiError } from "@/lib/api/client";
import { syncRun } from "@/test/msw/fixtures";

import { SyncResult } from "./SyncResult";

describe("SyncResult", () => {
  it("shows counts and outcome", () => {
    render(<SyncResult run={syncRun()} error={null} />);
    expect(screen.getByText("Added 10 · Updated 0 · Skipped 2 · Flagged 0")).toBeInTheDocument();
    expect(screen.getByText(/Sync finished \(manual\)/)).toBeInTheDocument();
  });

  it("shows the never-run message, request errors, run errors and hints", () => {
    const { rerender } = render(<SyncResult run={null} error={null} />);
    expect(screen.getByText(/No sync has run yet/)).toBeInTheDocument();
    rerender(
      <SyncResult run={null} error={new ApiError(429, "RATE_LIMITED", "Too many requests.")} />,
    );
    expect(screen.getByRole("alert")).toHaveTextContent("Too many requests.");
    const failed = syncRun({
      outcome: "failed",
      trigger: "startup",
      finished_at: null,
      error: { code: "PAYPAL_UNAVAILABLE", message: "PayPal is not responding." },
      hint: "New sandbox payments can take up to 3 hours.",
    });
    rerender(<SyncResult run={failed} error={null} />);
    expect(screen.getByText(/Sync failed \(on startup\)/)).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent("PayPal is not responding.");
    expect(screen.getByText(/up to 3 hours/)).toBeInTheDocument();
  });
});
