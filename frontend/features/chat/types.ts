import type { ChatOut } from "@/lib/api/chat-schemas";

/** `failure` holds the error message when the question could not be answered. */
export type UserMessage = { id: string; role: "user"; content: string; failure: string | null };
export type AssistantMessage = { id: string; role: "assistant"; reply: ChatOut };
export type ChatMessage = UserMessage | AssistantMessage;
