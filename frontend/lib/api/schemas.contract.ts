/**
 * Compile-time check that the zod schemas match the types generated from the backend
 * OpenAPI schema. If the backend changes, `npm run typecheck` fails here.
 */
import type { z } from "zod";

import type { components } from "./api-types";
import type { LastSyncSchema, SyncRunSchema, TransactionListSchema } from "./schemas";

type Api = components["schemas"];
type Same<A, B> = [A] extends [B] ? ([B] extends [A] ? true : false) : false;

export const contractChecks: [
  Same<z.infer<typeof SyncRunSchema>, Api["SyncRunOut"]>,
  Same<z.infer<typeof LastSyncSchema>, Api["SyncRunOut"] | null>,
  Same<z.infer<typeof TransactionListSchema>, Api["TransactionListOut"]>,
] = [true, true, true];
