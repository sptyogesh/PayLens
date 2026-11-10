import { render, screen, waitFor, within } from "@testing-library/react";

import { missingPayment } from "@/test/msw/fixtures";

import { MissingList } from "./MissingList";

describe("MissingList", () => {
  it("shows date, client, PayPal ID and gross of each payment without a FIRA", async () => {
    render(<MissingList rows={[missingPayment()]} />);
    const grid = screen.getByRole("region", { name: "Payments missing a FIRA" });
    await waitFor(() => {
      expect(within(grid).getByText("SEED-0022")).toBeInTheDocument();
    });
    expect(within(grid).getByText("20 Oct 2026")).toBeInTheDocument();
    expect(within(grid).getByText("Ben Hart")).toBeInTheDocument();
    expect(within(grid).getByText("£250.00")).toBeInTheDocument();
  });

  it("says so when every payment has a FIRA", () => {
    render(<MissingList rows={[]} />);
    expect(screen.getByText("Every payment has a FIRA")).toBeInTheDocument();
  });
});
