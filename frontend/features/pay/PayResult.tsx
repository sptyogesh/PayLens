import { ErrorState } from "@/components/ui/ErrorState";
import { MoneyText } from "@/components/ui/MoneyText";
import { Spinner } from "@/components/ui/Spinner";
import { PAY_TEXT } from "@/lib/constants";

import type { PayResultState } from "./usePayOrder";

/** Child of PayView: processing, confirmation or "no payment was made" (FR-034). */
export function PayResult({ result }: { result: PayResultState }) {
  if (result.status === "processing") return <Spinner label={PAY_TEXT.processing} />;
  if (result.status === "failed") return <ErrorState message={result.message} />;
  if (result.status !== "success") return null;
  const { capture } = result;
  return (
    <div
      role="status"
      className="rounded-lg border border-green-200 bg-green-50 p-4 text-sm text-green-900"
    >
      <p className="font-semibold">{PAY_TEXT.successTitle}</p>
      <p>
        <MoneyText amount={capture.gross.amount} currency={capture.gross.currency} />
      </p>
      <p>
        {PAY_TEXT.transactionIdLabel}:{" "}
        <span data-testid="transaction-id" className="font-mono">
          {capture.transaction_id}
        </span>
      </p>
      {capture.recorded ? null : <p>{PAY_TEXT.notRecorded}</p>}
    </div>
  );
}
