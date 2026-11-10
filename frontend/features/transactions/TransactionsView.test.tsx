import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";

import { syncRun, transaction, transactionList } from "@/test/msw/fixtures";
import { API } from "@/test/msw/handlers";
import { server } from "@/test/msw/server";

import { TransactionsView } from "./TransactionsView";

describe("TransactionsView", () => {
  it("syncs, shows the result and reloads the list", async () => {
    let listCalls = 0;
    server.use(
      http.get(`${API}/transactions`, () => {
        listCalls += 1;
        const items = listCalls === 1 ? [] : [transaction()];
        return HttpResponse.json(transactionList(items));
      }),
    );
    render(<TransactionsView />);
    expect(await screen.findByText("No transactions yet")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Sync now" }));
    expect(await screen.findByText(/Added 10/)).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText("PayPal sandbox")).toBeInTheDocument();
    });
  });

  it("shows the error state with retry when the list fails", async () => {
    let fail = true;
    server.use(
      http.get(`${API}/transactions`, () =>
        fail ? HttpResponse.error() : HttpResponse.json(transactionList([transaction()])),
      ),
    );
    render(<TransactionsView />);
    expect(await screen.findByText(/Cannot reach the PayLens server/)).toBeInTheDocument();
    fail = false;
    await userEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByText("PayPal sandbox")).toBeInTheDocument();
  });

  it("shows the last sync from the server on load", async () => {
    server.use(
      http.get(`${API}/sync/last`, () => HttpResponse.json(syncRun({ trigger: "startup" }))),
    );
    render(<TransactionsView />);
    expect(await screen.findByText(/Sync finished \(on startup\)/)).toBeInTheDocument();
  });
});
