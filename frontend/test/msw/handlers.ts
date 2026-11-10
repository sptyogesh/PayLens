import type { HttpHandler } from "msw";
import { http, HttpResponse } from "msw";

import {
  captureOut,
  chatAnswer,
  dashboard,
  firaList,
  firaUploadOut,
  syncRun,
  transactionList,
} from "./fixtures";

export const API = "http://api.test";
/** A tiny PDF-like body for the default GET /report.pdf mock. */
export const REPORT_PDF_BYTES = "%PDF-1.4\n% PayLens test report\n";

/** Default API mock handlers for unit tests. Tests override per case with server.use(). */
export const handlers: HttpHandler[] = [
  http.get(`${API}/transactions`, () => HttpResponse.json(transactionList())),
  http.get(`${API}/dashboard`, () => HttpResponse.json(dashboard())),
  http.get(`${API}/sync/last`, () => HttpResponse.json(null)),
  http.post(`${API}/sync`, () => HttpResponse.json(syncRun())),
  http.post(`${API}/pay/orders`, () => HttpResponse.json({ order_id: "ORDER1" }, { status: 201 })),
  http.post(`${API}/pay/orders/:orderId/capture`, () => HttpResponse.json(captureOut())),
  http.post(`${API}/chat`, () => HttpResponse.json(chatAnswer())),
  http.get(`${API}/fira`, () => HttpResponse.json(firaList())),
  http.get(`${API}/report.pdf`, ({ request }) => {
    const period = new URL(request.url).searchParams.get("period") ?? "last_3_months";
    return new HttpResponse(new Blob([REPORT_PDF_BYTES], { type: "application/pdf" }), {
      headers: {
        "Content-Type": "application/pdf",
        "Content-Disposition": `attachment; filename="paylens-ca-report-${period}-2026-11-10.pdf"`,
      },
    });
  }),
  http.post(`${API}/fira/upload`, ({ request }) => {
    const fileName = new URL(request.url).searchParams.get("file_name") ?? "";
    return HttpResponse.json(firaUploadOut({ file_name: fileName }));
  }),
];
