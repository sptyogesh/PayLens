import { chatAnswer } from "@/test/msw/fixtures";

import { toHistory, withAnswer, withFailure } from "./chatMessages";
import type { AssistantMessage, ChatMessage, UserMessage } from "./types";

const question = (id: string, content: string, failure: string | null = null): UserMessage => ({
  id,
  role: "user",
  content,
  failure,
});
const answer = (id: string, text: string): AssistantMessage => ({
  id,
  role: "assistant",
  reply: chatAnswer({ answer: text }),
});

describe("toHistory", () => {
  it("keeps only the last 6 turns, using the answer text for assistant turns", () => {
    const messages: ChatMessage[] = Array.from({ length: 8 }, (_, index) =>
      index % 2 === 0
        ? question(String(index), `Q${String(index)}`)
        : answer(String(index), `A${String(index)}`),
    );
    expect(toHistory(messages).map((turn) => turn.content)).toEqual([
      "Q2",
      "A3",
      "Q4",
      "A5",
      "Q6",
      "A7",
    ]);
  });

  it("trims long turns to the history item limit", () => {
    const long = "x".repeat(2500);
    const history = toHistory([question("1", long), answer("2", "ok")]);
    expect(history[0]?.content).toHaveLength(2000);
  });

  it("leaves out questions that have no answer (failed or pending)", () => {
    const messages = [
      question("1", "Q1"),
      answer("2", "A1"),
      question("3", "Failed", "Server down"),
      question("4", "Pending"),
    ];
    expect(toHistory(messages)).toEqual([
      { role: "user", content: "Q1" },
      { role: "assistant", content: "A1" },
    ]);
  });
});

describe("withAnswer / withFailure", () => {
  it("puts a retried answer right after its question", () => {
    const messages = [question("1", "Old", "Down"), question("2", "New"), answer("3", "A2")];
    const ids = withAnswer(withFailure(messages, "1", null), "1", answer("4", "A1")).map(
      (message) => message.id,
    );
    expect(ids).toEqual(["1", "4", "2", "3"]);
  });

  it("marks only the given question as failed", () => {
    const marked = withFailure([question("1", "A"), question("2", "B")], "2", "Down");
    expect(marked.map((message) => (message.role === "user" ? message.failure : null))).toEqual([
      null,
      "Down",
    ]);
  });
});
