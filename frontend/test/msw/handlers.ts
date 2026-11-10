import type { HttpHandler } from "msw";
import { http, HttpResponse } from "msw";

import { syncRun, transactionList } from "./fixtures";

export const API = "http://api.test";

/** Default API mock handlers for unit tests. Tests override per case with server.use(). */
export const handlers: HttpHandler[] = [
  http.get(`${API}/transactions`, () => HttpResponse.json(transactionList())),
  http.get(`${API}/sync/last`, () => HttpResponse.json(null)),
  http.post(`${API}/sync`, () => HttpResponse.json(syncRun())),
];
