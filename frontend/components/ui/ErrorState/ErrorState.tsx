import { MESSAGES } from "@/lib/constants";

import { Button } from "../Button";

export type ErrorStateProps = { message: string; onRetry?: () => void };

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div
      role="alert"
      className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-900"
    >
      <p>{message}</p>
      {onRetry ? (
        <Button variant="secondary" className="mt-3" onClick={onRetry}>
          {MESSAGES.retry}
        </Button>
      ) : null}
    </div>
  );
}
