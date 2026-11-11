import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";

import { SegmentedControl } from "./SegmentedControl";

type Period = "month" | "quarter" | "year";

const OPTIONS = [
  { value: "month", label: "This month" },
  { value: "quarter", label: "This quarter" },
  { value: "year", label: "This year" },
] as const;

function Controlled({ onChange }: { onChange: (value: Period) => void }) {
  const [value, setValue] = useState<Period>("month");
  return (
    <SegmentedControl<Period>
      label="Period"
      options={OPTIONS}
      value={value}
      onChange={(next) => {
        setValue(next);
        onChange(next);
      }}
    />
  );
}

describe("SegmentedControl", () => {
  it("renders the group label and every option as a radio", () => {
    render(
      <SegmentedControl label="Period" options={OPTIONS} value="quarter" onChange={vi.fn()} />,
    );
    expect(screen.getByRole("group", { name: "Period" })).toBeInTheDocument();
    expect(screen.getAllByRole("radio")).toHaveLength(OPTIONS.length);
    expect(screen.getByRole("radio", { name: "This quarter" })).toBeChecked();
    expect(screen.getByRole("radio", { name: "This month" })).not.toBeChecked();
  });

  it("calls onChange with the clicked option's value", async () => {
    const onChange = vi.fn();
    render(<SegmentedControl label="Period" options={OPTIONS} value="month" onChange={onChange} />);
    await userEvent.click(screen.getByText("This year"));
    expect(onChange).toHaveBeenCalledWith("year");
  });

  it("moves the selection with arrow keys", async () => {
    const onChange = vi.fn();
    render(<Controlled onChange={onChange} />);
    await userEvent.tab();
    expect(screen.getByRole("radio", { name: "This month" })).toHaveFocus();
    await userEvent.keyboard("{ArrowRight}");
    expect(onChange).toHaveBeenLastCalledWith("quarter");
    expect(screen.getByRole("radio", { name: "This quarter" })).toBeChecked();
  });
});
