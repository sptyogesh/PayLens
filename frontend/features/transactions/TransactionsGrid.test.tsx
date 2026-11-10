import { render, screen, waitFor, within } from "@testing-library/react";

import { transaction } from "@/test/msw/fixtures";

import { TransactionsGrid } from "./TransactionsGrid";

describe("TransactionsGrid", () => {
  it("shows a source badge on every row and formats money", async () => {
    const rows = [
      transaction({ id: "a" }),
      transaction({ id: "b", source: "demo_seed", is_flagged: true }),
    ];
    render(<TransactionsGrid rows={rows} />);
    const grid = screen.getByRole("region", { name: "Transactions" });
    await waitFor(() => {
      expect(within(grid).getAllByText(/PayPal sandbox|Demo seed/)).toHaveLength(2);
    });
    expect(within(grid).getAllByText("$100.00")).toHaveLength(2);
    expect(within(grid).getByText("Check")).toBeInTheDocument();
  });

  it("shows the empty state without rows", () => {
    render(<TransactionsGrid rows={[]} />);
    expect(screen.getByText("No transactions yet")).toBeInTheDocument();
  });
});
