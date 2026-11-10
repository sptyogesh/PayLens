/** Must match backend app/common/constants.py (CHAT_QUESTION_MAX, CHAT_HISTORY_*). */
export const CHAT_QUESTION_MAX = 500;
export const CHAT_HISTORY_MAX = 6;
export const CHAT_HISTORY_ITEM_MAX = 2000;
/** Backend CHAT_DEADLINE_S (30 s) plus a margin for the network. */
export const CHAT_CLIENT_TIMEOUT_MS = 40_000;

export const SUGGESTED_QUESTIONS = [
  "How much FX loss last quarter?",
  "Which client costs me the most in fees?",
  "What was my income this financial year?",
  "Show my 5 largest payments",
] as const;

export const CHAT_TEXT = {
  title: "Ask your money",
  intro:
    "Answers come only from your PayLens data. Every number is computed by PayLens, not by the AI.",
  suggestedTitle: "Try one of these questions",
  conversationLabel: "Conversation",
  userLabel: "You",
  assistantLabel: "PayLens assistant",
  inputLabel: "Your question",
  inputHint: "Press Enter to send, Shift+Enter for a new line.",
  counter: (length: number) => `${length} / ${CHAT_QUESTION_MAX} characters`,
  send: "Send",
  thinking: "Thinking…",
  notAnswered: "Not answered",
  periodPrefix: "Period:",
  basedOn: "Based on",
  fallbackNotice:
    "The assistant could not give a full answer. Any figures shown are computed by PayLens.",
  /** Figure labels containing this are losses where a negative value is a gain. */
  fxLossMarker: "FX loss",
} as const;
