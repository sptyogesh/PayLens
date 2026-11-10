import { render, screen, waitFor, within } from "@testing-library/react";

import { transaction } from "@/test/msw/fixtures";

import { TransactionsGrid } from "../TransactionsGrid";

describe("FIRA column", () => {
  it("shows a FIRA badge per payment and a dash when there is none", async () => {
    render(
      <TransactionsGrid
        rows={[
          transaction({ id: "a", fira_status: "matched" }),
          transaction({ id: "b", fira_status: "needs_review" }),
          transaction({ id: "c", fira_status: "missing" }),
          transaction({ id: "d", fira_status: null }),
        ]}
      />,
    );
    const grid = screen.getByRole("region", { name: "Transactions" });
    await waitFor(() => {
      expect(within(grid).getByText("Missing")).toHaveAttribute("data-variant", "missing");
    });
    expect(within(grid).getByRole("columnheader", { name: "FIRA" })).toBeInTheDocument();
    expect(within(grid).getByText("Matched")).toHaveAttribute("data-variant", "matched");
    expect(within(grid).getByText("Needs review")).toHaveAttribute("data-variant", "needs_review");
    expect(within(grid).getAllByText("—")).toHaveLength(1);
  });
});
