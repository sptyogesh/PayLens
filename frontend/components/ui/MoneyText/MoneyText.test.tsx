import { render, screen } from "@testing-library/react";

import { MoneyText } from "./MoneyText";

describe("MoneyText", () => {
  it("formats a string amount with its currency", () => {
    render(<MoneyText amount="77914.00" currency="INR" />);
    expect(screen.getByText("₹77,914.00")).toBeInTheDocument();
  });

  it("U4 shows a negative FX value as a gain", () => {
    render(<MoneyText amount="-120.50" currency="INR" gainWhenNegative />);
    expect(screen.getByText(/₹120\.50/)).toBeInTheDocument();
    expect(screen.getByText("(Gain)")).toBeInTheDocument();
  });

  it("keeps the minus sign when not a gain", () => {
    render(<MoneyText amount="-5.00" currency="USD" />);
    expect(screen.getByText(/-\$5\.00/)).toBeInTheDocument();
  });
});
