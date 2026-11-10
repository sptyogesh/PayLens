"use client";

/**
 * Parent for /chat. Children: SuggestedQuestions (before the first question), MessageList
 * (questions, answers and their figures) and ChatInput. State and POST /chat live in useChat.
 */
import { PageHeader } from "@/components/layout/PageHeader";
import { Card } from "@/components/ui/Card";
import { Spinner } from "@/components/ui/Spinner";
import { CHAT_TEXT } from "@/lib/constants";

import { ChatInput } from "./ChatInput";
import { MessageList } from "./MessageList";
import { SuggestedQuestions } from "./SuggestedQuestions";
import { useChat } from "./useChat";

export function ChatPanel() {
  const chat = useChat();
  return (
    <>
      <PageHeader title={CHAT_TEXT.title} />
      <div className="mx-auto max-w-3xl min-w-0 space-y-4">
        <p className="text-sm text-slate-700">{CHAT_TEXT.intro}</p>
        {chat.messages.length === 0 ? (
          <SuggestedQuestions disabled={chat.isPending} onPick={chat.send} />
        ) : null}
        <MessageList messages={chat.messages} onRetry={chat.retry} />
        {chat.isPending ? <Spinner label={CHAT_TEXT.thinking} /> : null}
        <Card>
          <ChatInput isPending={chat.isPending} onSend={chat.send} />
        </Card>
      </div>
    </>
  );
}
