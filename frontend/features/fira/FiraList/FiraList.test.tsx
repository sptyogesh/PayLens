import { render, screen, waitFor, within } from "@testing-library/react";

import { firaItem } from "@/test/msw/fixtures";

import { FiraList } from "./FiraList";

describe("FiraList", () => {
  it("shows extracted fields, status badge, score and linked payments", async () => {
    render(<FiraList rows={[firaItem({ score: 95 })]} />);
    const grid = screen.getByRole("region", { name: "FIRAs" });
    await waitFor(() => {
      expect(within(grid).getByText("fira-SEED-0001.pdf")).toBeInTheDocument();
    });
    expect(within(grid).getByText("Matched")).toHaveAttribute("data-variant", "matched");
    expect(within(grid).getByText("$100.00")).toBeInTheDocument();
    expect(within(grid).getByText("₹8,400.00")).toBeInTheDocument();
    expect(within(grid).getByText("11 Nov 2026")).toBeInTheDocument();
    expect(within(grid).getByText("95")).toBeInTheDocument();
    expect(within(grid).getAllByText("3C679366HH908993F")).toHaveLength(2);
  });

  it("shows dashes for missing fields and a neutral No match badge", async () => {
    const row = firaItem({
      status: "no_match",
      score: null,
      reason: null,
      foreign_amount: null,
      inr_amount: null,
      remittance_date: null,
      reference_no: null,
      matches: [],
    });
    render(<FiraList rows={[row]} />);
    const grid = screen.getByRole("region", { name: "FIRAs" });
    await waitFor(() => {
      expect(within(grid).getByText("No match")).toBeInTheDocument();
    });
    expect(within(grid).getAllByText("—")).toHaveLength(7);
  });

  it("lists every payment of a weekly match", async () => {
    const matches = ["P-1", "P-2"].map((id) => ({
      transaction_id: id,
      paypal_transaction_id: id,
      score: 60,
      kind: "weekly" as const,
    }));
    render(<FiraList rows={[firaItem({ status: "needs_review", matches })]} />);
    expect(await screen.findByText("P-1, P-2")).toBeInTheDocument();
  });

  it("shows the empty state without FIRAs", () => {
    render(<FiraList rows={[]} />);
    expect(screen.getByText("No FIRAs uploaded yet")).toBeInTheDocument();
  });
});
