/** Pure helpers for the /chat conversation list (used by useChat). */
import type { ChatTurn } from "@/lib/api/chat-schemas";
import { CHAT_HISTORY_ITEM_MAX, CHAT_HISTORY_MAX } from "@/lib/constants";

import type { AssistantMessage, ChatMessage } from "./types";

/** True when the message is an answer, or a question followed by its answer. */
function isAnsweredTurn(message: ChatMessage, index: number, messages: ChatMessage[]): boolean {
  return message.role === "assistant" || messages[index + 1]?.role === "assistant";
}

/**
 * The last CHAT_HISTORY_MAX answered turns, in the shape POST /chat expects. Questions with no
 * answer (failed or still pending) are left out so they do not pollute the next question.
 */
export function toHistory(messages: ChatMessage[]): ChatTurn[] {
  return messages
    .filter(isAnsweredTurn)
    .slice(-CHAT_HISTORY_MAX)
    .map((message) => ({
      role: message.role,
      content: (message.role === "user" ? message.content : message.reply.answer).slice(
        0,
        CHAT_HISTORY_ITEM_MAX,
      ),
    }));
}

/** Set (or clear, with null) the failure of the question `userId`. */
export function withFailure(
  messages: ChatMessage[],
  userId: string,
  failure: string | null,
): ChatMessage[] {
  return messages.map((message) =>
    message.id === userId && message.role === "user" ? { ...message, failure } : message,
  );
}

/** Put the answer right after its question, so a retried old question keeps its place. */
export function withAnswer(
  messages: ChatMessage[],
  userId: string,
  answer: AssistantMessage,
): ChatMessage[] {
  const index = messages.findIndex((message) => message.id === userId);
  if (index < 0) return [...messages, answer];
  return [...messages.slice(0, index + 1), answer, ...messages.slice(index + 1)];
}
