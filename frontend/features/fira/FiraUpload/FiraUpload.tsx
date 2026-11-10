"use client";

import { FileUpload } from "@/components/ui/FileUpload";
import { Spinner } from "@/components/ui/Spinner";
import { FIRA_TEXT } from "@/lib/constants";

import { UploadResults } from "./UploadResults";
import { useFiraUpload } from "./useFiraUpload";

/** Child of FiraView: pick PDFs, upload them one by one, then list each file's result. */
export function FiraUpload({ onUploaded }: { onUploaded: () => void }) {
  const { progress, results, upload } = useFiraUpload(onUploaded);
  return (
    <div className="space-y-4">
      <FileUpload
        label={FIRA_TEXT.uploadLabel}
        hint={FIRA_TEXT.uploadHint}
        disabled={progress !== null}
        onFiles={(files) => {
          void upload(files);
        }}
      />
      {progress ? <Spinner label={FIRA_TEXT.uploading(progress.current, progress.total)} /> : null}
      <UploadResults results={results} />
    </div>
  );
}
