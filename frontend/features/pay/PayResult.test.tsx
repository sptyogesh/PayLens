import { render, screen } from "@testing-library/react";

import { captureOut } from "@/test/msw/fixtures";

import { PayResult } from "./PayResult";

describe("PayResult", () => {
  it("renders nothing when idle and a spinner while processing", () => {
    const { container, rerender } = render(<PayResult result={{ status: "idle" }} />);
    expect(container).toBeEmptyDOMElement();
    rerender(<PayResult result={{ status: "processing" }} />);
    expect(screen.getByRole("status")).toHaveTextContent("Processing payment…");
  });

  it("shows the amount from the capture", () => {
    render(<PayResult result={{ status: "success", capture: captureOut() }} />);
    expect(screen.getByText("$50.00")).toBeInTheDocument();
  });
});
