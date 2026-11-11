import { render, screen } from "@testing-library/react";

import { Card } from "./Card";

describe("Card", () => {
  it("renders title and content", () => {
    render(<Card title="Last sync">body</Card>);
    expect(screen.getByRole("heading", { name: "Last sync" })).toBeInTheDocument();
    expect(screen.getByText("body")).toBeInTheDocument();
  });

  it("renders without a title", () => {
    render(<Card>only body</Card>);
    expect(screen.queryByRole("heading")).not.toBeInTheDocument();
  });
});
