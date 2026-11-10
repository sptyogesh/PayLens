"use client";

import type { KeyboardEvent } from "react";
import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { TextArea } from "@/components/ui/TextArea";
import { CHAT_QUESTION_MAX, CHAT_TEXT } from "@/lib/constants";

export type ChatInputProps = {
  isPending: boolean;
  onSend: (question: string) => void;
};

const INPUT_ROWS = 2;

/** Enter sends; Shift+Enter (or Enter while composing text) adds a new line. */
function sendOnEnter(submit: () => void) {
  return (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key !== "Enter" || event.shiftKey || event.nativeEvent.isComposing) return;
    event.preventDefault();
    submit();
  };
}

/** Child of ChatPanel: the question field and Send button (disabled when empty, U9). */
export function ChatInput({ isPending, onSend }: ChatInputProps) {
  const [text, setText] = useState("");
  const canSend = text.trim().length > 0 && !isPending;

  const submit = () => {
    if (!canSend) return;
    onSend(text);
    setText("");
  };

  return (
    <form
      className="space-y-2"
      onSubmit={(event) => {
        event.preventDefault();
        submit();
      }}
    >
      <TextArea
        label={CHAT_TEXT.inputLabel}
        value={text}
        rows={INPUT_ROWS}
        maxLength={CHAT_QUESTION_MAX}
        hint={`${CHAT_TEXT.counter(text.length)}. ${CHAT_TEXT.inputHint}`}
        onKeyDown={sendOnEnter(submit)}
        onValueChange={setText}
      />
      <div className="flex justify-end">
        <Button type="submit" disabled={!canSend}>
          {CHAT_TEXT.send}
        </Button>
      </div>
    </form>
  );
}
