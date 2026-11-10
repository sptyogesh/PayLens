import { render, screen } from "@testing-library/react";

import { DISCLAIMERS } from "@/lib/constants";

import { Disclaimer } from "./Disclaimer";

describe("Disclaimer (U11)", () => {
  it.each(["notTaxAdvice", "simulated", "sandboxCheckout", "demoMode"] as const)(
    "shows the %s text from constants",
    (kind) => {
      render(<Disclaimer kind={kind} />);
      expect(screen.getByRole("note")).toHaveTextContent(DISCLAIMERS[kind]);
    },
  );
});
