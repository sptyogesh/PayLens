import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";

import type { ChatIn } from "@/lib/api/chat-schemas";
import { chatAnswer } from "@/test/msw/fixtures";
import { API } from "@/test/msw/handlers";
import { server } from "@/test/msw/server";

import { ChatPanel } from "./ChatPanel";

const NOT_TAX_ADVICE = "Prepared from user data — not tax advice. Confirm with a CA.";

async function ask(question: string) {
  await userEvent.type(screen.getByLabelText("Your question"), question);
  await userEvent.click(screen.getByRole("button", { name: "Send" }));
}

const assistantBubbles = () => screen.findAllByRole("article", { name: "PayLens assistant" });

function captureBodies(): ChatIn[] {
  const bodies: ChatIn[] = [];
  server.use(
    http.post(`${API}/chat`, async ({ request }) => {
      bodies.push((await request.json()) as ChatIn);
      return HttpResponse.json(chatAnswer({ answer: `Answer ${String(bodies.length)}` }));
    }),
  );
  return bodies;
}

const errorReply = (status: number, code: string, message: string) =>
  http.post(`${API}/chat`, () => HttpResponse.json({ error: { code, message } }, { status }), {
    once: true,
  });

describe("ChatPanel", () => {
  it("shows the intro, suggestions and a disabled Send button at first", () => {
    render(<ChatPanel />);
    expect(screen.getByRole("heading", { name: "Ask your money" })).toBeVisible();
    expect(screen.getByText(/computed by PayLens, not by the AI/)).toBeVisible();
    expect(screen.getByRole("button", { name: "Send" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "How much FX loss last quarter?" })).toBeVisible();
  });

  it("shows the question, then the answer with figures, period and disclaimer", async () => {
    server.use(
      http.post(`${API}/chat`, () => HttpResponse.json(chatAnswer({ disclaimer: NOT_TAX_ADVICE }))),
    );
    render(<ChatPanel />);
    await ask("How much FX loss last quarter?");
    expect(screen.getByRole("article", { name: "You" })).toHaveTextContent(
      "How much FX loss last quarter?",
    );
    const [bubble] = await assistantBubbles();
    if (!bubble) throw new Error("no answer");
    expect(bubble).toHaveTextContent(/Your FX loss in last quarter/);
    expect(within(bubble).getByRole("list", { name: "Based on" })).toHaveTextContent("₹38,000.00");
    expect(bubble).toHaveTextContent("Period: Last quarter (1 Jul 2026 – 30 Sep 2026)");
    expect(within(bubble).getByRole("note")).toHaveTextContent(NOT_TAX_ADVICE);
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });

  it("shows Thinking… while the answer is pending", async () => {
    let release = () => {};
    const gate = new Promise<void>((resolve) => {
      release = resolve;
    });
    server.use(
      http.post(`${API}/chat`, async () => {
        await gate;
        return HttpResponse.json(chatAnswer());
      }),
    );
    render(<ChatPanel />);
    await ask("Hi");
    expect(await screen.findByRole("status")).toHaveTextContent("Thinking…");
    expect(screen.getByRole("button", { name: "Send" })).toBeDisabled();
    release();
    await assistantBubbles();
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });

  it("sends the previous turns as history with the second question", async () => {
    const bodies = captureBodies();
    render(<ChatPanel />);
    await ask("  First?  ");
    await screen.findByText("Answer 1");
    await ask("And the month before?");
    await screen.findByText("Answer 2");
    expect(bodies[0]).toEqual({ question: "First?", history: [] });
    expect(bodies[1]).toEqual({
      question: "And the month before?",
      history: [
        { role: "user", content: "First?" },
        { role: "assistant", content: "Answer 1" },
      ],
    });
  });

  it("sends a suggested question when it is clicked", async () => {
    const bodies = captureBodies();
    render(<ChatPanel />);
    await userEvent.click(screen.getByRole("button", { name: "Show my 5 largest payments" }));
    await screen.findByText("Answer 1");
    expect(bodies[0]?.question).toBe("Show my 5 largest payments");
    expect(screen.queryByRole("button", { name: "Show my 5 largest payments" })).toBeNull();
  });

  it("shows the fallback notice for a fallback answer", async () => {
    server.use(
      http.post(`${API}/chat`, () => HttpResponse.json(chatAnswer({ outcome: "fallback" }))),
    );
    render(<ChatPanel />);
    await ask("Hi");
    const [bubble] = await assistantBubbles();
    expect(bubble).toHaveTextContent(/could not give a full answer/);
  });

  it.each([
    [429, "RATE_LIMITED", "Too many questions. Please wait a minute."],
    [500, "INTERNAL", "Something went wrong. Please try again."],
  ])("shows the %i error and retries the same question", async (status, code, message) => {
    const bodies: ChatIn[] = [];
    server.use(
      http.post(`${API}/chat`, async ({ request }) => {
        bodies.push((await request.json()) as ChatIn);
        return HttpResponse.json(chatAnswer());
      }),
    );
    server.use(errorReply(status, code, message));
    render(<ChatPanel />);
    await ask("Fees?");
    expect(await screen.findByRole("alert")).toHaveTextContent(message);
    await userEvent.click(screen.getByRole("button", { name: "Try again" }));
    await assistantBubbles();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(bodies).toEqual([{ question: "Fees?", history: [] }]);
    expect(screen.getAllByRole("article", { name: "You" })).toHaveLength(1);
  });

  it("shows an error when a money figure is not a string", async () => {
    const bad = { ...chatAnswer(), figures: [{ ...chatAnswer().figures[0], value: 38000 }] };
    server.use(http.post(`${API}/chat`, () => HttpResponse.json(bad)));
    render(<ChatPanel />);
    await ask("Hi");
    expect(await screen.findByRole("alert")).toHaveTextContent(/unexpected format/);
    expect(screen.queryByRole("article", { name: "PayLens assistant" })).toBeNull();
  });

  it("keeps a failed question out of the next question's history", async () => {
    const bodies = captureBodies();
    server.use(errorReply(500, "INTERNAL", "Something went wrong. Please try again."));
    render(<ChatPanel />);
    await ask("Fees?");
    expect(await screen.findByText("Not answered")).toBeVisible();
    await ask("Income?");
    await screen.findByText("Answer 1");
    expect(bodies).toEqual([{ question: "Income?", history: [] }]);
    expect(screen.getByText("Not answered")).toBeVisible();
  });

  it("retries an older failed question with its own history and answers it in place", async () => {
    const bodies = captureBodies();
    server.use(errorReply(500, "INTERNAL", "Something went wrong. Please try again."));
    render(<ChatPanel />);
    await ask("Fees?");
    await screen.findByText("Not answered");
    await ask("Income?");
    await screen.findByText("Answer 1");
    await userEvent.click(screen.getByRole("button", { name: "Try again" }));
    await screen.findByText("Answer 2");
    expect(bodies[1]).toEqual({ question: "Fees?", history: [] });
    expect(screen.queryByText("Not answered")).not.toBeInTheDocument();
    const turns = screen.getAllByRole("article").map((turn) => turn.textContent);
    expect(turns[0]).toContain("Fees?");
    expect(turns[1]).toContain("Answer 2");
    expect(turns[2]).toContain("Income?");
  });
});
