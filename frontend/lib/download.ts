/** Save a Blob as a file: object URL → temporary <a download> click → revoke the URL. */
import { OBJECT_URL_REVOKE_DELAY_MS } from "./constants";

export function downloadBlob(blob: Blob, fileName: string): void {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = fileName;
  link.style.display = "none";
  document.body.append(link);
  try {
    link.click();
  } finally {
    link.remove();
    // Some browsers read the URL after click() returns, so revoke it a moment later.
    setTimeout(() => {
      URL.revokeObjectURL(url);
    }, OBJECT_URL_REVOKE_DELAY_MS);
  }
}
