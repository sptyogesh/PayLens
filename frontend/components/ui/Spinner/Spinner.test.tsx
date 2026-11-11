import { render, screen } from "@testing-library/react";

import { Spinner } from "./Spinner";

describe("Spinner", () => {
  it("announces loading with a default label", () => {
    render(<Spinner />);
    expect(screen.getByRole("status")).toHaveTextContent("Loading…");
  });

  it("uses a custom label", () => {
    render(<Spinner label="Syncing…" />);
    expect(screen.getByRole("status")).toHaveTextContent("Syncing…");
  });
});
