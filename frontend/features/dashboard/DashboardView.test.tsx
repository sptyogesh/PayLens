import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";

import { dashboard, totals } from "@/test/msw/fixtures";
import { API } from "@/test/msw/handlers";
import { server } from "@/test/msw/server";

import { DashboardView } from "./DashboardView";

describe("DashboardView", () => {
  it("loads the default period and reloads when the period changes", async () => {
    const periods: (string | null)[] = [];
    server.use(
      http.get(`${API}/dashboard`, ({ request }) => {
        const period = new URL(request.url).searchParams.get("period");
        periods.push(period);
        const count = period === "all_time" ? 24 : 2;
        return HttpResponse.json(dashboard({ totals: totals({ payment_count: count }) }));
      }),
    );
    render(<DashboardView />);
    expect(await screen.findByText("2 payments")).toBeVisible();
    expect(screen.getByRole("radio", { name: "Last 3 months" })).toBeChecked();
    await userEvent.click(screen.getByRole("radio", { name: "All time" }));
    expect(await screen.findByText("24 payments")).toBeVisible();
    expect(periods).toEqual(["last_3_months", "all_time"]);
  });

  it("U3 rejects numeric money and shows the error state with retry", async () => {
    let invalid = true;
    server.use(
      http.get(`${API}/dashboard`, () => {
        const body = dashboard();
        return HttpResponse.json(
          invalid
            ? { ...body, totals: { ...body.totals, income_inr: { amount: 1, currency: "INR" } } }
            : body,
        );
      }),
    );
    render(<DashboardView />);
    expect(await screen.findByText(/unexpected format/)).toBeVisible();
    invalid = false;
    await userEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByText("2 payments")).toBeVisible();
  });
});
