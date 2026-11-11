import { render, screen } from "@testing-library/react";

import { DataGrid } from "./DataGrid";

type Row = { id: string; name: string };

describe("DataGrid", () => {
  it("U7 shows EmptyState when there are no rows", () => {
    render(
      <DataGrid<Row>
        rows={[]}
        columns={[{ field: "name" }]}
        label="Transactions"
        emptyTitle="No transactions yet"
        emptyMessage="Press Sync now"
      />,
    );
    expect(screen.getByText("No transactions yet")).toBeInTheDocument();
    expect(screen.getByText("Press Sync now")).toBeInTheDocument();
    expect(screen.queryByRole("region", { name: "Transactions" })).not.toBeInTheDocument();
  });

  it("renders a labelled grid region when there are rows", () => {
    render(
      <DataGrid<Row>
        rows={[{ id: "1", name: "Acme" }]}
        columns={[{ field: "name", headerName: "Client" }]}
        label="Transactions"
        emptyTitle="No transactions yet"
        getRowId={(row) => row.id}
      />,
    );
    expect(screen.getByRole("region", { name: "Transactions" })).toBeInTheDocument();
  });

  it("grows with its rows when autoHeight is set", () => {
    render(
      <DataGrid<Row>
        rows={[{ id: "1", name: "A" }]}
        columns={[{ field: "name" }]}
        label="Small table"
        emptyTitle="Empty"
        autoHeight
      />,
    );
    expect(screen.getByRole("region", { name: "Small table" })).not.toHaveStyle({
      height: "480px",
    });
  });
});
