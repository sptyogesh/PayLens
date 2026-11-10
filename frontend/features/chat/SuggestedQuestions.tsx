import { Button } from "@/components/ui/Button";
import { CHAT_TEXT, SUGGESTED_QUESTIONS } from "@/lib/constants";

export type SuggestedQuestionsProps = {
  disabled: boolean;
  onPick: (question: string) => void;
};

/** Child of ChatPanel: one-click example questions, shown before the first question. */
export function SuggestedQuestions({ disabled, onPick }: SuggestedQuestionsProps) {
  return (
    <section aria-labelledby="suggested-questions" className="space-y-2">
      <h2 id="suggested-questions" className="text-sm font-semibold text-slate-800">
        {CHAT_TEXT.suggestedTitle}
      </h2>
      <ul className="flex flex-wrap gap-2">
        {SUGGESTED_QUESTIONS.map((question) => (
          <li key={question} className="max-w-full">
            <Button
              variant="secondary"
              className="text-left"
              disabled={disabled}
              onClick={() => {
                onPick(question);
              }}
            >
              {question}
            </Button>
          </li>
        ))}
      </ul>
    </section>
  );
}
