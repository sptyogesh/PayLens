import { render, screen, within } from "@testing-library/react";

import { MoneyText } from "../MoneyText";
import { StatCard } from "./StatCard";

describe("StatCard (U5)", () => {
  it("renders title, MoneyText value and hint", () => {
    render(
      <StatCard
        title="Received"
        value={<MoneyText amount="77914.00" currency="INR" />}
        hint="Last 30 days"
      />,
    );
    const card = screen.getByRole("group", { name: "Received" });
    expect(within(card).getByText("Received")).toBeInTheDocument();
    expect(within(card).getByText("₹77,914.00")).toBeInTheDocument();
    expect(within(card).getByText("Last 30 days")).toBeInTheDocument();
  });

  it("renders no hint when none is given", () => {
    render(<StatCard title="Fees" value="12" />);
    const card = screen.getByRole("group", { name: "Fees" });
    expect(card).toHaveTextContent(/^Fees12$/);
  });
});
