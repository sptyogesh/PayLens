import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { TextArea } from "./TextArea";

describe("TextArea", () => {
  it("reports typed values and links the hint and error", async () => {
    const onValueChange = vi.fn();
    const { rerender } = render(
      <TextArea label="Question" value="" hint="0 / 10" onValueChange={onValueChange} />,
    );
    await userEvent.type(screen.getByLabelText("Question"), "a");
    expect(onValueChange).toHaveBeenCalledWith("a");
    expect(screen.getByRole("textbox")).toHaveAccessibleDescription("0 / 10");
    expect(screen.getByRole("textbox")).toHaveAttribute("aria-invalid", "false");

    rerender(
      <TextArea label="Question" value="a" error="Too long" onValueChange={onValueChange} />,
    );
    expect(screen.getByRole("textbox")).toHaveAttribute("aria-invalid", "true");
    expect(screen.getByRole("textbox")).toHaveAccessibleDescription("Too long");
  });
});
