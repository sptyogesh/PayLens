import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";

import { captureOut } from "@/test/msw/fixtures";
import { API } from "@/test/msw/handlers";
import { server } from "@/test/msw/server";

import { PayView } from "./PayView";

async function fillAmount(amount: string) {
  await userEvent.type(screen.getByLabelText("Amount"), amount);
}

describe("PayView (test-mode button)", () => {
  it("keeps the button disabled until the form is valid and shows field errors", async () => {
    render(<PayView />);
    const button = screen.getByRole("button", { name: "Pay (test mode)" });
    expect(button).toBeDisabled();
    await fillAmount("1.234");
    expect(screen.getByText(/at most 2 decimals/)).toBeInTheDocument();
    expect(button).toBeDisabled();
    expect(screen.getByText(/Sandbox demo — no real money/)).toBeInTheDocument();
  });

  it("pays and shows the confirmation with the transaction ID", async () => {
    render(<PayView />);
    await fillAmount("50");
    await userEvent.selectOptions(screen.getByLabelText("Currency"), "GBP");
    await userEvent.click(screen.getByRole("button", { name: "Pay (test mode)" }));
    expect(await screen.findByText("Payment received")).toBeInTheDocument();
    expect(screen.getByText("3C679366HH908993F")).toBeInTheDocument();
  });

  it("explains when the payment was captured but not recorded yet", async () => {
    server.use(
      http.post(`${API}/pay/orders/:orderId/capture`, () =>
        HttpResponse.json(captureOut({ recorded: false })),
      ),
    );
    render(<PayView />);
    await fillAmount("50");
    await userEvent.click(screen.getByRole("button", { name: "Pay (test mode)" }));
    expect(await screen.findByText(/after the next sync/)).toBeInTheDocument();
  });

  it("shows 'No payment was made' when PayPal declines", async () => {
    server.use(
      http.post(`${API}/pay/orders/:orderId/capture`, () =>
        HttpResponse.json(
          {
            error: {
              code: "PAYMENT_DECLINED",
              message: "PayPal did not approve this payment. No payment was made.",
            },
          },
          { status: 422 },
        ),
      ),
    );
    render(<PayView />);
    await fillAmount("13.13");
    await userEvent.click(screen.getByRole("button", { name: "Pay (test mode)" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("No payment was made.");
  });

  it("shows the error when the order cannot be created", async () => {
    server.use(
      http.post(`${API}/pay/orders`, () =>
        HttpResponse.json(
          { error: { code: "RATE_LIMITED", message: "Too many requests." } },
          { status: 429 },
        ),
      ),
    );
    render(<PayView />);
    await fillAmount("50");
    await userEvent.click(screen.getByRole("button", { name: "Pay (test mode)" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Too many requests.");
  });
});
