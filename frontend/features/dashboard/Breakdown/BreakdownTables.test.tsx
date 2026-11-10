import { render, screen, waitFor, within } from "@testing-library/react";

import { breakdownRow, dashboard, totals } from "@/test/msw/fixtures";

import { BreakdownTables } from "./BreakdownTables";

const inr = (amount: string) => ({ amount, currency: "INR" });

describe("BreakdownTables", () => {
  it("shows one row per month and per client with API values", async () => {
    const data = dashboard({
      by_month: [breakdownRow("2026-11", "Nov 2026"), breakdownRow("2026-10", "Oct 2026")],
      by_client: [breakdownRow("c-1", "Ava Stone", totals({ fx_loss_inr: inr("-10.00") }))],
    });
    render(<BreakdownTables data={data} />);
    const months = screen.getByRole("region", { name: "Leakage by month" });
    await waitFor(() => {
      expect(within(months).getByText("Nov 2026")).toBeInTheDocument();
    });
    expect(within(months).getByText("Oct 2026")).toBeInTheDocument();
    expect(within(months).getAllByText("₹1,269.92")).toHaveLength(2);
    const clients = screen.getByRole("region", { name: "Leakage by client" });
    expect(within(clients).getByText("Ava Stone")).toBeInTheDocument();
    expect(within(clients).getByText("(Gain)")).toBeInTheDocument();
    expect(within(clients).getByText("7.56%")).toBeInTheDocument();
  });

  it("renders nothing for an empty period", () => {
    const { container } = render(<BreakdownTables data={dashboard({ totals: null })} />);
    expect(container).toBeEmptyDOMElement();
  });
});
