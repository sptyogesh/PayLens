import { toOrderBody, validatePayForm } from "./payForm";

const valid = { amount: "50", currency: "USD", description: "Logo design" } as const;

describe("validatePayForm (FR-031)", () => {
  it("accepts a valid order", () => {
    expect(validatePayForm({ ...valid }).order).not.toBeNull();
    expect(validatePayForm({ ...valid, amount: "10000.00" }).order).not.toBeNull();
  });

  it.each([
    ["", "Enter an amount"],
    ["0", "more than 0"],
    ["0.00", "more than 0"],
    ["-5", "Enter an amount"],
    ["1.234", "Enter an amount"],
    ["10000.01", "at most 10000.00"],
    ["abc", "Enter an amount"],
  ])("rejects amount %j", (amount, message) => {
    const { order, errors } = validatePayForm({ ...valid, amount });
    expect(order).toBeNull();
    expect(errors.amount).toContain(message);
  });

  it("limits the description to 127 characters", () => {
    expect(validatePayForm({ ...valid, description: "x".repeat(127) }).order).not.toBeNull();
    expect(
      validatePayForm({ ...valid, description: "x".repeat(128) }).errors.description,
    ).toBeDefined();
  });
});

describe("toOrderBody", () => {
  it("normalises the amount and omits a blank description", () => {
    expect(toOrderBody({ ...valid, amount: "5.5", description: "  " })).toEqual({
      amount: "5.50",
      currency: "USD",
    });
    expect(toOrderBody({ ...valid })).toEqual({
      amount: "50.00",
      currency: "USD",
      description: "Logo design",
    });
  });
});
