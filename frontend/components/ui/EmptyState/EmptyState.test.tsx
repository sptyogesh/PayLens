import { render, screen } from "@testing-library/react";

import { EmptyState } from "./EmptyState";

describe("EmptyState", () => {
  it("shows title, message and action", () => {
    render(
      <EmptyState
        title="No transactions yet"
        message="Press Sync now"
        action={<button>Go</button>}
      />,
    );
    expect(screen.getByText("No transactions yet")).toBeInTheDocument();
    expect(screen.getByText("Press Sync now")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Go" })).toBeInTheDocument();
  });

  it("shows only the title when nothing else is given", () => {
    render(<EmptyState title="Nothing" />);
    expect(screen.getByText("Nothing")).toBeInTheDocument();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });
});
