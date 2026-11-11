import { render, screen } from "@testing-library/react";

import { PageHeader } from "./PageHeader";

describe("PageHeader", () => {
  it("shows the title and the demo-mode banner", () => {
    render(<PageHeader title="Transactions" actions={<button>Sync now</button>} />);
    expect(screen.getByRole("heading", { level: 1, name: "Transactions" })).toBeInTheDocument();
    expect(screen.getByRole("note")).toHaveTextContent("Demo mode — PayPal sandbox data");
    expect(screen.getByRole("button", { name: "Sync now" })).toBeInTheDocument();
  });
});
