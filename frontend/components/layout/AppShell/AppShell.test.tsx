import { render, screen } from "@testing-library/react";

import { AppShell } from "./AppShell";

vi.mock("next/navigation", () => ({ usePathname: () => "/transactions" }));

describe("AppShell", () => {
  it("renders navigation and marks the current page", () => {
    render(<AppShell>content</AppShell>);
    expect(screen.getByRole("navigation", { name: "Main" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Transactions" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(screen.getByRole("link", { name: "Pay (sandbox)" })).not.toHaveAttribute("aria-current");
    expect(screen.getByRole("main")).toHaveTextContent("content");
  });
});
