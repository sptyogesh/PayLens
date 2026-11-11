import { render, screen, waitFor, within } from "@testing-library/react";

import { leakage, transaction } from "@/test/msw/fixtures";

import { TransactionsGrid } from "./TransactionsGrid";

async function renderGrid(rows: Parameters<typeof TransactionsGrid>[0]["rows"]) {
  render(<TransactionsGrid rows={rows} />);
  const grid = screen.getByRole("region", { name: "Transactions" });
  await waitFor(() => {
    expect(within(grid).getAllByText(/PayPal sandbox|Demo seed/)).toHaveLength(rows.length);
  });
  return grid;
}

describe("TransactionsGrid", () => {
  it("shows a source badge on every row and formats money", async () => {
    const grid = await renderGrid([
      transaction({ id: "a" }),
      transaction({ id: "b", source: "demo_seed", is_flagged: true }),
    ]);
    expect(within(grid).getAllByText("$100.00")).toHaveLength(2);
    expect(within(grid).getByText("Check")).toBeInTheDocument();
  });

  it("shows leakage in INR with the simulated label on the PayPal rate", async () => {
    const grid = await renderGrid([transaction()]);
    expect(within(grid).getByText("PayPal rate (Simulated (sandbox))")).toBeInTheDocument();
    expect(within(grid).getByText("₹81.480000")).toBeInTheDocument();
    expect(within(grid).getByText("₹634.96")).toBeInTheDocument();
    expect(within(grid).getByText("7.56%")).toBeInTheDocument();
  });

  it("shows an FX gain instead of a negative loss", async () => {
    const gain = leakage({ fx_loss_inr: { amount: "-12.00", currency: "INR" } });
    const grid = await renderGrid([transaction({ leakage: gain })]);
    expect(within(grid).getByText("Gain", { exact: false })).toBeInTheDocument();
  });

  it("says 'Rate unavailable' without inventing numbers", async () => {
    const row = transaction({ leakage_status: "rate_unavailable", leakage: null });
    const grid = await renderGrid([row]);
    expect(within(grid).getAllByText("Rate unavailable")).toHaveLength(7);
    expect(within(grid).queryByText(/₹/)).not.toBeInTheDocument();
  });

  it("shows the empty state without rows", () => {
    render(<TransactionsGrid rows={[]} />);
    expect(screen.getByText("No transactions yet")).toBeInTheDocument();
  });
});
