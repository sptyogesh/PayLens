import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactNode } from "react";

import { PayPalCheckoutButton } from "./PayPalCheckoutButton";

type MockButtonProps = {
  disabled: boolean;
  createOrder: () => Promise<{ orderId: string }>;
  onApprove: (data: { orderId: string }) => Promise<void>;
  onCancel: () => void;
};

vi.mock("@paypal/react-paypal-js/sdk-v6", () => ({
  PayPalProvider: ({ children, environment }: { children: ReactNode; environment: string }) => (
    <div data-environment={environment}>{children}</div>
  ),
  PayPalOneTimePaymentButton: (props: MockButtonProps) => (
    <>
      <button
        disabled={props.disabled}
        onClick={() => void props.createOrder().then((data) => props.onApprove(data))}
      >
        PayPal
      </button>
      <button onClick={props.onCancel}>Cancel at PayPal</button>
    </>
  ),
}));

const order = { amount: "50", currency: "USD", description: "" } as const;

describe("PayPalCheckoutButton (SDK v6 mocked)", () => {
  it("uses the sandbox, creates the order on the backend and captures on approve", async () => {
    const createOrder = vi.fn().mockResolvedValue("ORDER1");
    const capture = vi.fn().mockResolvedValue(undefined);
    render(
      <PayPalCheckoutButton
        order={order}
        createOrder={createOrder}
        capture={capture}
        fail={vi.fn()}
      />,
    );
    expect(screen.getByRole("button", { name: "PayPal" }).parentElement).toHaveAttribute(
      "data-environment",
      "sandbox",
    );
    await userEvent.click(screen.getByRole("button", { name: "PayPal" }));
    expect(createOrder).toHaveBeenCalledWith(order);
    expect(capture).toHaveBeenCalledWith("ORDER1");
  });

  it("is disabled without a valid order and reports a cancel as no payment", async () => {
    const fail = vi.fn();
    render(
      <PayPalCheckoutButton order={null} createOrder={vi.fn()} capture={vi.fn()} fail={fail} />,
    );
    expect(screen.getByRole("button", { name: "PayPal" })).toBeDisabled();
    await userEvent.click(screen.getByRole("button", { name: "Cancel at PayPal" }));
    expect(fail).toHaveBeenCalledWith("No payment was made.");
  });
});
