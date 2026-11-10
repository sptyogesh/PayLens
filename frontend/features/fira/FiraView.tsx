"use client";

/**
 * Parent for the FIRA page. Children: FiraUpload (picker + per-file results), FiraSummary
 * (counts), FiraList (uploaded FIRAs) and MissingList (payments without a FIRA).
 * Data comes from useFira; an upload reloads it.
 */
import { PageHeader } from "@/components/layout/PageHeader";
import { Card } from "@/components/ui/Card";
import { ErrorState } from "@/components/ui/ErrorState";
import { Spinner } from "@/components/ui/Spinner";
import { FIRA_TEXT } from "@/lib/constants";

import { FiraList } from "./FiraList";
import { FiraSummary } from "./FiraSummary";
import { FiraUpload } from "./FiraUpload";
import { MissingList } from "./MissingList";
import { useFira } from "./useFira";

export function FiraView() {
  const fira = useFira();
  return (
    <>
      <PageHeader title={FIRA_TEXT.title} />
      <div className="space-y-6">
        <p className="max-w-3xl text-sm text-slate-700">{FIRA_TEXT.explainer}</p>
        <Card>
          <FiraUpload onUploaded={fira.reload} />
        </Card>
        {fira.status === "loading" ? <Spinner /> : null}
        {fira.status === "error" ? (
          <ErrorState message={fira.error.message} onRetry={fira.reload} />
        ) : null}
        {fira.status === "success" ? (
          <>
            <FiraSummary summary={fira.data.summary} />
            <Card title={FIRA_TEXT.listTitle}>
              <FiraList rows={fira.data.items} />
            </Card>
            <Card title={FIRA_TEXT.missingTitle}>
              <MissingList rows={fira.data.missing} />
            </Card>
          </>
        ) : null}
      </div>
    </>
  );
}
