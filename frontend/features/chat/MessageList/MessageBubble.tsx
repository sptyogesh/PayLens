import { Disclaimer } from "@/components/ui/Disclaimer";
import { ErrorState } from "@/components/ui/ErrorState";
import { CHAT_TEXT } from "@/lib/constants";

import type { AssistantMessage, ChatMessage, UserMessage } from "../types";

import { FigureList } from "./FigureList";

const BUBBLE_CLASS = "max-w-full rounded-lg px-4 py-3 text-sm break-words sm:max-w-[85%]";

export type MessageBubbleProps = { message: ChatMessage; onRetry: (userId: string) => void };

/** Child of MessageList: one question or one answer with its period, figures and disclaimer. */
export function MessageBubble({ message, onRetry }: MessageBubbleProps) {
  if (message.role === "user") return <UserBubble message={message} onRetry={onRetry} />;
  return <AssistantBubble message={message} />;
}

function UserBubble({ message, onRetry }: { message: UserMessage; onRetry: (id: string) => void }) {
  return (
    <div className="ml-auto flex max-w-full flex-col items-end gap-2 sm:max-w-[85%]">
      <article
        aria-label={CHAT_TEXT.userLabel}
        className={`${BUBBLE_CLASS} bg-blue-700 whitespace-pre-wrap text-white`}
      >
        {message.content}
      </article>
      {message.failure === null ? null : (
        <div className="w-full">
          <p className="mb-1 text-right text-xs font-semibold text-red-900">
            {CHAT_TEXT.notAnswered}
          </p>
          <ErrorState
            message={message.failure}
            onRetry={() => {
              onRetry(message.id);
            }}
          />
        </div>
      )}
    </div>
  );
}

function AssistantBubble({ message }: { message: AssistantMessage }) {
  const { reply } = message;
  return (
    <article
      aria-label={CHAT_TEXT.assistantLabel}
      className={`${BUBBLE_CLASS} border border-slate-200 bg-white text-slate-900`}
    >
      {reply.outcome === "fallback" ? (
        <p className="mb-2 text-xs text-amber-900">{CHAT_TEXT.fallbackNotice}</p>
      ) : null}
      <p className="whitespace-pre-wrap">{reply.answer}</p>
      {reply.periods.length > 0 ? (
        <p className="mt-2 text-xs text-slate-600">
          {CHAT_TEXT.periodPrefix} {reply.periods.join("; ")}
        </p>
      ) : null}
      <FigureList figures={reply.figures} />
      {reply.disclaimer ? (
        <div className="mt-3">
          <Disclaimer text={reply.disclaimer} />
        </div>
      ) : null}
    </article>
  );
}
