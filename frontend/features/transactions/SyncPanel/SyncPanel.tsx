import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Spinner } from "@/components/ui/Spinner";
import { SYNC_TEXT } from "@/lib/constants";

import type { SyncState } from "../useSync";
import { SyncResult } from "./SyncResult";

/** Child of TransactionsView: the Sync now button and the last result (FR-019). */
export function SyncPanel({ sync }: { sync: SyncState }) {
  return (
    <Card title="PayPal sandbox sync">
      <div className="mb-3 flex flex-wrap items-center gap-3">
        <Button onClick={() => void sync.syncNow()} disabled={sync.running}>
          {SYNC_TEXT.button}
        </Button>
        {sync.running ? <Spinner label={SYNC_TEXT.running} /> : null}
      </div>
      <SyncResult run={sync.lastRun} error={sync.error} />
    </Card>
  );
}
