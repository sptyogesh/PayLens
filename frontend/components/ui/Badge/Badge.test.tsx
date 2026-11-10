import { render, screen } from "@testing-library/react";

import type { BadgeVariant } from "./Badge";
import { Badge } from "./Badge";

describe("Badge (U6)", () => {
  it.each<[BadgeVariant, string]>([
    ["paypal_sandbox", "PayPal sandbox"],
    ["demo_seed", "Demo seed"],
    ["matched", "Matched"],
    ["needs_review", "Needs review"],
    ["missing", "Missing"],
  ])("%s shows %s with its own style", (variant, label) => {
    render(<Badge variant={variant} />);
    const badge = screen.getByText(label);
    expect(badge).toHaveAttribute("data-variant", variant);
    expect(badge.className).toMatch(/bg-\w+-100/);
  });
});
