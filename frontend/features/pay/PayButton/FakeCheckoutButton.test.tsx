import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import type { PayFormValues } from "../payForm";

import { FakeCheckoutButton } from "./FakeCheckoutButton";

const ORDER: PayFormValues = { amount: "50", currency: "USD", description: "" };

describe("FakeCheckoutButton", () => {
  it("is disabled while the payment is processing, so a double click sends one order", async () => {
    let release = () => {};
    const gate = new Promise<void>((resolve) => {
      release = resolve;
    });
    const createOrder = vi.fn(async () => {
      await gate;
      return "ORDER1";
    });
    const capture = vi.fn(async () => {});
    render(
      <FakeCheckoutButton
        order={ORDER}
        createOrder={createOrder}
        capture={capture}
        fail={vi.fn()}
      />,
    );
    const button = screen.getByRole("button", { name: "Pay (test mode)" });
    await userEvent.dblClick(button);
    expect(button).toBeDisabled();
    release();
    await waitFor(() => {
      expect(button).toBeEnabled();
    });
    expect(createOrder).toHaveBeenCalledOnce();
    expect(capture).toHaveBeenCalledWith("ORDER1");
  });
});
