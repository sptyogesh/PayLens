import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ChatInput } from "./ChatInput";

function setup(isPending = false) {
  const onSend = vi.fn();
  render(<ChatInput isPending={isPending} onSend={onSend} />);
  return { onSend, field: screen.getByLabelText("Your question") };
}

describe("ChatInput", () => {
  it("U9 keeps Send disabled for empty or whitespace text", async () => {
    const { field } = setup();
    const send = screen.getByRole("button", { name: "Send" });
    expect(send).toBeDisabled();
    await userEvent.type(field, "   ");
    expect(send).toBeDisabled();
    await userEvent.type(field, "Hi");
    expect(send).toBeEnabled();
  });

  it("keeps Send disabled while an answer is pending", async () => {
    const { field } = setup(true);
    await userEvent.type(field, "Hi");
    expect(screen.getByRole("button", { name: "Send" })).toBeDisabled();
  });

  it("sends on Enter, clears the field, and adds a new line on Shift+Enter", async () => {
    const { onSend, field } = setup();
    await userEvent.type(field, "first{Shift>}{Enter}{/Shift}line");
    expect(onSend).not.toHaveBeenCalled();
    expect(field).toHaveValue("first\nline");
    await userEvent.type(field, "{Enter}");
    expect(onSend).toHaveBeenCalledWith("first\nline");
    expect(field).toHaveValue("");
  });

  it("does not send whitespace on Enter and shows the character counter", async () => {
    const { onSend, field } = setup();
    await userEvent.type(field, "  {Enter}");
    expect(onSend).not.toHaveBeenCalled();
    expect(field).toHaveAttribute("maxLength", "500");
    expect(field).toHaveAccessibleDescription(/2 \/ 500 characters/);
  });
});
