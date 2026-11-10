import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { TextField } from "./TextField";

describe("TextField", () => {
  it("reports typed values and links the error message", async () => {
    const onValueChange = vi.fn();
    const { rerender } = render(
      <TextField label="Amount" value="" onValueChange={onValueChange} />,
    );
    await userEvent.type(screen.getByLabelText("Amount"), "5");
    expect(onValueChange).toHaveBeenCalledWith("5");
    expect(screen.getByLabelText("Amount")).toHaveAttribute("aria-invalid", "false");

    rerender(
      <TextField label="Amount" value="5" error="Too small" onValueChange={onValueChange} />,
    );
    const input = screen.getByRole("textbox");
    expect(input).toHaveAttribute("aria-invalid", "true");
    expect(input).toHaveAccessibleDescription("Too small");
  });
});
