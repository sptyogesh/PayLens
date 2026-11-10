import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { FileUpload } from "./FileUpload";

const MB = 1024 * 1024;

function pdf(name = "fira.pdf", size = 10): File {
  const file = new File(["%PDF-1.4"], name, { type: "application/pdf" });
  Object.defineProperty(file, "size", { value: size });
  return file;
}

function setup(props: Partial<Parameters<typeof FileUpload>[0]> = {}) {
  const onFiles = vi.fn();
  render(<FileUpload label="FIRA PDFs" hint="PDF only" onFiles={onFiles} {...props} />);
  const input = screen.getByLabelText("FIRA PDFs");
  return { onFiles, input };
}

describe("FileUpload (U10)", () => {
  it("passes valid PDFs to onFiles without an error", async () => {
    const { onFiles, input } = setup();
    const files = [pdf("a.pdf"), pdf("b.pdf")];
    await userEvent.upload(input, files);
    expect(onFiles).toHaveBeenCalledWith(files);
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(input).toHaveAccessibleDescription("PDF only");
  });

  it("rejects a non-PDF with a clear message and does not call onFiles", async () => {
    const { onFiles, input } = setup();
    const text = new File(["hello"], "notes.txt", { type: "text/plain" });
    await userEvent.upload(input, text, { applyAccept: false });
    expect(screen.getByRole("alert")).toHaveTextContent("notes.txt is not a PDF");
    expect(onFiles).not.toHaveBeenCalled();
  });

  it("rejects a file over 5 MB and does not call onFiles", async () => {
    const { onFiles, input } = setup();
    await userEvent.upload(input, pdf("big.pdf", 5 * MB + 1));
    expect(screen.getByRole("alert")).toHaveTextContent("big.pdf is larger than 5 MB");
    expect(onFiles).not.toHaveBeenCalled();
  });

  it("accepts exactly 5 MB and rejects an empty file", async () => {
    const { onFiles, input } = setup();
    const ok = pdf("ok.pdf", 5 * MB);
    await userEvent.upload(input, [ok, pdf("empty.pdf", 0)]);
    expect(onFiles).toHaveBeenCalledWith([ok]);
    expect(screen.getByRole("alert")).toHaveTextContent("empty.pdf is empty");
  });

  it("rejects a selection with too many files", async () => {
    const { onFiles, input } = setup({ limits: { maxBytes: 5 * MB, maxFiles: 2 } });
    await userEvent.upload(input, [pdf("a.pdf"), pdf("b.pdf"), pdf("c.pdf")]);
    expect(screen.getByRole("alert")).toHaveTextContent("Choose at most 2 files");
    expect(onFiles).not.toHaveBeenCalled();
  });

  it("can be disabled", () => {
    const { input } = setup({ disabled: true });
    expect(input).toBeDisabled();
  });
});
