import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { chatAnswer } from "@/test/msw/fixtures";

import { MessageList } from "./MessageList";

const noop = () => {};

describe("MessageList", () => {
  it("shows answer, period and figures formatted for display", () => {
    render(
      <MessageList
        onRetry={noop}
        messages={[{ id: "a", role: "assistant", reply: chatAnswer() }]}
      />,
    );
    const log = screen.getByRole("log", { name: "Conversation" });
    const figures = within(log).getByRole("list", { name: "Based on" });
    const items = within(figures).getAllByRole("listitem");
    expect(items[0]).toHaveTextContent("FX loss: ₹38,000.00");
    expect(items[1]).toHaveTextContent("Payments: 18");
    expect(items[2]).toHaveTextContent("Leakage %: 7.30%");
    expect(within(log).getByText(/^Period: Last quarter/)).toBeVisible();
    expect(within(log).queryByRole("note")).not.toBeInTheDocument();
  });

  it("shows a negative FX loss as a gain", () => {
    const reply = chatAnswer({
      figures: [{ label: "FX loss", kind: "money", value: "-50.00", currency: "INR", period: "p" }],
    });
    render(<MessageList onRetry={noop} messages={[{ id: "a", role: "assistant", reply }]} />);
    expect(screen.getByRole("listitem")).toHaveTextContent("₹50.00 (Gain)");
  });

  it("shows the fallback notice and no figure list when there are no figures", () => {
    const reply = chatAnswer({ outcome: "fallback", figures: [], periods: [] });
    render(<MessageList onRetry={noop} messages={[{ id: "a", role: "assistant", reply }]} />);
    expect(screen.getByText(/could not give a full answer/)).toBeVisible();
    expect(screen.queryByRole("list")).not.toBeInTheDocument();
    expect(screen.queryByText(/^Period:/)).not.toBeInTheDocument();
  });

  it("labels user and assistant turns", () => {
    render(
      <MessageList
        onRetry={noop}
        messages={[
          { id: "u", role: "user", content: "How much?", failure: null },
          { id: "a", role: "assistant", reply: chatAnswer() },
        ]}
      />,
    );
    expect(screen.getByRole("article", { name: "You" })).toHaveTextContent("How much?");
    expect(screen.getByRole("article", { name: "PayLens assistant" })).toBeVisible();
  });

  it("marks a failed question as not answered with its own retry", async () => {
    const onRetry = vi.fn();
    render(
      <MessageList
        onRetry={onRetry}
        messages={[{ id: "u1", role: "user", content: "Fees?", failure: "Server down" }]}
      />,
    );
    expect(screen.getByText("Not answered")).toBeVisible();
    expect(screen.getByRole("alert")).toHaveTextContent("Server down");
    await userEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(onRetry).toHaveBeenCalledWith("u1");
  });
});
