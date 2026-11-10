import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { Button } from "./Button";

describe("Button", () => {
  it("calls onClick and defaults to type=button", async () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Sync now</Button>);
    const button = screen.getByRole("button", { name: "Sync now" });
    expect(button).toHaveAttribute("type", "button");
    await userEvent.click(button);
    expect(onClick).toHaveBeenCalledOnce();
  });

  it("does not fire when disabled", async () => {
    const onClick = vi.fn();
    render(
      <Button variant="secondary" disabled onClick={onClick}>
        Pay
      </Button>,
    );
    await userEvent.click(screen.getByRole("button", { name: "Pay" }));
    expect(onClick).not.toHaveBeenCalled();
  });
});
