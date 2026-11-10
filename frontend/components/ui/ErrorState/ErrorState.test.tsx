import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ErrorState } from "./ErrorState";

describe("ErrorState", () => {
  it("shows the message as an alert with retry", async () => {
    const onRetry = vi.fn();
    render(<ErrorState message="PayPal is not responding." onRetry={onRetry} />);
    expect(screen.getByRole("alert")).toHaveTextContent("PayPal is not responding.");
    await userEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(onRetry).toHaveBeenCalledOnce();
  });

  it("hides retry when no handler is given", () => {
    render(<ErrorState message="Bad" />);
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });
});
