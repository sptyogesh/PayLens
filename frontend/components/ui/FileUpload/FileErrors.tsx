import { FILE_UPLOAD_TEXT } from "@/lib/constants";

/** Child of FileUpload: one line per rejected file. */
export function FileErrors({ errors }: { errors: string[] }) {
  if (errors.length === 0) return null;
  return (
    <div role="alert" className="rounded-md border border-red-200 bg-red-50 p-3 text-sm">
      <p className="font-medium text-red-900">{FILE_UPLOAD_TEXT.errorsTitle}</p>
      <ul className="mt-1 list-disc pl-5 text-red-900">
        {errors.map((error, index) => (
          <li key={`${String(index)}-${error}`}>{error}</li>
        ))}
      </ul>
    </div>
  );
}
