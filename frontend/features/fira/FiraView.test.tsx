import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";

import { firaList, firaSummary, firaUploadOut } from "@/test/msw/fixtures";
import { API } from "@/test/msw/handlers";
import { server } from "@/test/msw/server";

import { FiraView } from "./FiraView";

const pdf = (name: string) => new File(["%PDF-1.4"], name, { type: "application/pdf" });

function countUploads() {
  const seen: { name: string | null; type: string | null }[] = [];
  server.use(
    http.post(`${API}/fira/upload`, ({ request }) => {
      const name = new URL(request.url).searchParams.get("file_name");
      seen.push({ name, type: request.headers.get("content-type") });
      return HttpResponse.json(firaUploadOut({ file_name: name ?? "" }));
    }),
  );
  return seen;
}

const card = (name: string) => screen.getByRole("group", { name });

describe("FiraView", () => {
  it("shows the explainer, summary counts, FIRAs and missing payments", async () => {
    render(<FiraView />);
    expect(screen.getByRole("heading", { name: "FIRA matching" })).toBeVisible();
    expect(screen.getByText(/proof that a foreign payment reached India/)).toBeVisible();
    await screen.findByRole("group", { name: "Matched" });
    expect(within(card("Matched")).getByText("1")).toBeVisible();
    expect(within(card("No match")).getByText("0")).toBeVisible();
    expect(within(card("Payments missing a FIRA")).getByText("1")).toBeVisible();
    const list = screen.getByRole("region", { name: "FIRAs" });
    await waitFor(() => {
      expect(within(list).getByText("fira-SEED-0020.pdf")).toBeInTheDocument();
    });
    const missing = screen.getByRole("region", { name: "Payments missing a FIRA" });
    await waitFor(() => {
      expect(within(missing).getByText("SEED-0022")).toBeInTheDocument();
    });
  });

  it("uploads files one by one as raw PDFs, lists results and reloads the summary", async () => {
    const uploads = countUploads();
    let listCalls = 0;
    server.use(
      http.get(`${API}/fira`, () => {
        listCalls += 1;
        const summary = firaSummary({ matched: listCalls === 1 ? 1 : 3 });
        return HttpResponse.json(firaList({ summary }));
      }),
    );
    render(<FiraView />);
    await screen.findByRole("group", { name: "Matched" });
    await userEvent.upload(screen.getByLabelText("FIRA PDFs"), [pdf("a b.pdf"), pdf("c.pdf")]);
    const results = await screen.findByRole("list", { name: "Upload results" });
    await waitFor(() => {
      expect(within(results).getAllByText("Stored")).toHaveLength(2);
    });
    expect(uploads).toEqual([
      { name: "a b.pdf", type: "application/pdf" },
      { name: "c.pdf", type: "application/pdf" },
    ]);
    await waitFor(() => {
      expect(within(card("Matched")).getByText("3")).toBeVisible();
    });
  });

  it("U10 sends no request for a non-PDF and shows why", async () => {
    const uploads = countUploads();
    render(<FiraView />);
    const text = new File(["hi"], "notes.txt", { type: "text/plain" });
    await userEvent.upload(screen.getByLabelText("FIRA PDFs"), text, { applyAccept: false });
    expect(screen.getByRole("alert")).toHaveTextContent("notes.txt is not a PDF");
    expect(uploads).toHaveLength(0);
  });

  it("keeps going after a failed file and shows the server's message", async () => {
    let calls = 0;
    server.use(
      http.post(`${API}/fira/upload`, () => {
        calls += 1;
        if (calls === 1) {
          const error = { code: "RATE_LIMITED", message: "Too many uploads. Wait a minute." };
          return HttpResponse.json({ error }, { status: 429 });
        }
        return HttpResponse.json(
          firaUploadOut({ outcome: "duplicate", message: "Already uploaded." }),
        );
      }),
    );
    render(<FiraView />);
    await userEvent.upload(screen.getByLabelText("FIRA PDFs"), [pdf("a.pdf"), pdf("b.pdf")]);
    const results = await screen.findByRole("list", { name: "Upload results" });
    await waitFor(() => {
      expect(within(results).getByText("Duplicate")).toBeVisible();
    });
    expect(within(results).getByText("Failed")).toBeVisible();
    expect(within(results).getByText("Too many uploads. Wait a minute.")).toBeVisible();
    expect(within(results).getByText("Already uploaded.")).toBeVisible();
  });

  it("shows progress while uploading", async () => {
    let release: () => void = () => undefined;
    const gate = new Promise<void>((resolve) => {
      release = resolve;
    });
    server.use(
      http.post(`${API}/fira/upload`, async () => {
        await gate;
        return HttpResponse.json(firaUploadOut());
      }),
    );
    render(<FiraView />);
    await userEvent.upload(screen.getByLabelText("FIRA PDFs"), [pdf("a.pdf"), pdf("b.pdf")]);
    expect(await screen.findByText("Uploading 1 of 2…")).toBeVisible();
    expect(screen.getByLabelText("FIRA PDFs")).toBeDisabled();
    release();
    await waitFor(() => {
      expect(screen.getByLabelText("FIRA PDFs")).toBeEnabled();
    });
  });

  it("shows an error with retry when the list fails", async () => {
    let fail = true;
    server.use(
      http.get(`${API}/fira`, () => (fail ? HttpResponse.error() : HttpResponse.json(firaList()))),
    );
    render(<FiraView />);
    expect(await screen.findByText(/Cannot reach the PayLens server/)).toBeVisible();
    fail = false;
    await userEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByRole("group", { name: "Matched" })).toBeVisible();
  });
});
