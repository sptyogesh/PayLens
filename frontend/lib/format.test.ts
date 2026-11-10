import { absoluteAmount, formatDate, formatINR, formatMoney, isNegativeAmount } from "./format";

describe("formatINR", () => {
  it("U1 formats rupees with en-IN grouping", () => {
    expect(formatINR("77914.00")).toBe("₹77,914.00");
  });

  it("U2 uses lakh grouping", () => {
    expect(formatINR("1234567.50")).toBe("₹12,34,567.50");
  });

  it("keeps exact decimals from the string (no float rounding)", () => {
    expect(formatINR("0.10")).toBe("₹0.10");
    expect(formatINR("9007199254740993.01")).toBe("₹9,00,71,99,25,47,40,993.01");
  });
});

describe("formatMoney", () => {
  it.each([
    ["USD", "$"],
    ["GBP", "£"],
    ["EUR", "€"],
    ["AUD", "A$"],
  ])("shows the %s symbol", (currency, symbol) => {
    expect(formatMoney("50.00", currency)).toContain(symbol);
    expect(formatMoney("50.00", currency)).toContain("50.00");
  });
});

describe("amount sign helpers", () => {
  it("detects negatives and strips the sign without arithmetic", () => {
    expect(isNegativeAmount("-12.50")).toBe(true);
    expect(isNegativeAmount("12.50")).toBe(false);
    expect(absoluteAmount("-12.50")).toBe("12.50");
    expect(absoluteAmount("12.50")).toBe("12.50");
  });
});

describe("formatDate", () => {
  it("shows UTC times in IST", () => {
    expect(formatDate("2026-11-10T06:30:00Z")).toContain("12:00");
  });
});
