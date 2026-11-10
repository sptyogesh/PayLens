import type { HttpHandler } from "msw";

/** Default API mock handlers for unit tests. Tests override per case with server.use(). */
export const handlers: HttpHandler[] = [];
