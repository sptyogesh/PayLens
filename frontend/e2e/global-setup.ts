import { resetDatabase } from "./support/db";

/** Start every run from an empty e2e database. */
export default function globalSetup(): void {
  resetDatabase();
}
