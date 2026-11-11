import { CHAT_TEXT } from "@/lib/constants";

import type { ChatMessage } from "../types";

import { MessageBubble } from "./MessageBubble";

/**
 * Child of ChatPanel: the conversation as a live log. Grandchildren: MessageBubble (one turn)
 * and FigureList (the "Based on" figures under an answer).
 */
export function MessageList({
  messages,
  onRetry,
}: {
  messages: ChatMessage[];
  onRetry: (userId: string) => void;
}) {
  return (
    <div
      role="log"
      aria-live="polite"
      aria-label={CHAT_TEXT.conversationLabel}
      className="flex min-w-0 flex-col gap-3"
    >
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} onRetry={onRetry} />
      ))}
    </div>
  );
}
