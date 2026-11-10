import { render, screen, within } from "@testing-library/react";

import { dashboard, totals } from "@/test/msw/fixtures";

import { LeakageSummary } from "./LeakageSummary";

const inr = (amount: string) => ({ amount, currency: "INR" });

describe("LeakageSummary", () => {
  it("shows the five cards with values from the API", () => {
    render(<LeakageSummary data={dashboard()} />);
    const card = (name: string) => screen.getByRole("group", { name });
    expect(within(card("Total income (INR, mid-market)")).getByText("₹16,800.00")).toBeVisible();
    expect(within(card("Total income (INR, mid-market)")).getByText("2 payments")).toBeVisible();
    expect(within(card("Fee loss")).getByText("₹789.60")).toBeVisible();
    expect(within(card("FX loss (Simulated (sandbox))")).getByText("₹480.32")).toBeVisible();
    expect(within(card("Total leakage")).getByText("₹1,269.92")).toBeVisible();
    expect(within(card("Leakage %")).getByText("7.56%")).toBeVisible();
  });

  it("shows a negative FX loss as a gain", () => {
    render(<LeakageSummary data={dashboard({ totals: totals({ fx_loss_inr: inr("-50.00") }) })} />);
    const fx = screen.getByRole("group", { name: "FX loss (Simulated (sandbox))" });
    expect(within(fx).getByText("₹50.00")).toBeVisible();
    expect(within(fx).getByText("(Gain)")).toBeVisible();
  });

  it("names the period and sources and shows the simulated notice", () => {
    render(<LeakageSummary data={dashboard()} />);
    expect(screen.getByText("Last 3 months")).toBeVisible();
    expect(screen.getByText(/Includes: Demo seed, PayPal sandbox/)).toBeVisible();
    expect(screen.getByText(/minus 3.00%/)).toBeVisible();
  });

  it("shows an empty state instead of zero cards and counts excluded payments", () => {
    render(<LeakageSummary data={dashboard({ totals: null, excluded_count: 2, sources: [] })} />);
    expect(screen.getByText("No payments in this period")).toBeVisible();
    expect(screen.queryByRole("group", { name: "Fee loss" })).not.toBeInTheDocument();
    expect(screen.getByText(/2 payments are not included/)).toBeVisible();
  });

  it("explains rows that cannot be calculated separately from missing rates", () => {
    render(<LeakageSummary data={dashboard({ not_calculated_count: 1 })} />);
    expect(screen.getByText(/1 payment is not included because the PayPal fee/)).toBeVisible();
    expect(screen.queryByText(/exchange rate is unavailable/)).not.toBeInTheDocument();
  });

  it("shows a dash when the percentage is not available", () => {
    render(<LeakageSummary data={dashboard({ totals: totals({ leakage_percent: null }) })} />);
    expect(within(screen.getByRole("group", { name: "Leakage %" })).getByText("—")).toBeVisible();
  });
});
