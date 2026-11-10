"use client";

import { useRef, useState } from "react";

import { toApiError } from "@/hooks/useApi";
import type { ChatTurn } from "@/lib/api/chat-schemas";
import { ChatOutSchema } from "@/lib/api/chat-schemas";
import { apiPost } from "@/lib/api/client";
import { CHAT_CLIENT_TIMEOUT_MS } from "@/lib/constants";

import { toHistory, withAnswer, withFailure } from "./chatMessages";
import type { ChatMessage } from "./types";

export type ChatState = {
  messages: ChatMessage[];
  isPending: boolean;
  send: (question: string) => void;
  /** Ask a failed question again, with the history it had when it was first sent. */
  retry: (userId: string) => void;
};

/** Conversation state for /chat. The browser keeps the history; the server is stateless. */
export function useChat(): ChatState {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isPending, setIsPending] = useState(false);
  const nextId = useRef(0);
  const newId = () => `m-${String((nextId.current += 1))}`;

  const ask = async (userId: string, question: string, history: ChatTurn[]) => {
    setIsPending(true);
    setMessages((current) => withFailure(current, userId, null));
    try {
      const reply = await apiPost("/chat", { question, history }, ChatOutSchema, {
        timeoutMs: CHAT_CLIENT_TIMEOUT_MS,
      });
      const answer = { id: newId(), role: "assistant" as const, reply };
      setMessages((current) => withAnswer(current, userId, answer));
    } catch (caught) {
      setMessages((current) => withFailure(current, userId, toApiError(caught).message));
    } finally {
      setIsPending(false);
    }
  };

  const send = (question: string) => {
    const trimmed = question.trim();
    if (!trimmed || isPending) return;
    const id = newId();
    const history = toHistory(messages);
    setMessages((current) => [...current, { id, role: "user", content: trimmed, failure: null }]);
    void ask(id, trimmed, history);
  };

  const retry = (userId: string) => {
    const index = messages.findIndex((message) => message.id === userId);
    const message = messages[index];
    if (isPending || message?.role !== "user" || message.failure === null) return;
    void ask(userId, message.content, toHistory(messages.slice(0, index)));
  };

  return { messages, isPending, send, retry };
}
