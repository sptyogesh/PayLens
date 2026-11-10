import { downloadBlob } from "./download";

describe("downloadBlob", () => {
  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("clicks a temporary link with the file name, then revokes the object URL", () => {
    vi.useFakeTimers();
    const create = vi.fn(() => "blob:report");
    const revoke = vi.fn();
    Object.assign(URL, { createObjectURL: create, revokeObjectURL: revoke });
    const clicked: { href: string; download: string }[] = [];
    vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(function (
      this: HTMLAnchorElement,
    ) {
      clicked.push({ href: this.href, download: this.download });
    });
    const blob = new Blob(["%PDF-"], { type: "application/pdf" });

    downloadBlob(blob, "report.pdf");

    expect(create).toHaveBeenCalledWith(blob);
    expect(clicked).toEqual([{ href: "blob:report", download: "report.pdf" }]);
    expect(document.querySelector("a")).toBeNull();
    vi.runAllTimers();
    expect(revoke).toHaveBeenCalledWith("blob:report");
  });
});
