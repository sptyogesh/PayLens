import { render, screen } from "@testing-library/react";

import { FiraStatusBadge } from "./FiraStatusBadge";

describe("FiraStatusBadge", () => {
  it.each([
    ["matched", "Matched"],
    ["needs_review", "Needs review"],
    ["no_match", "No match"],
  ] as const)("%s shows %s", (status, label) => {
    render(<FiraStatusBadge status={status} />);
    expect(screen.getByText(label)).toHaveAttribute("data-variant", status);
  });
});
