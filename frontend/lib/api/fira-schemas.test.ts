import { firaList, firaUploadOut } from "@/test/msw/fixtures";

import { FiraListSchema, FiraUploadOutSchema } from "./fira-schemas";
import { TransactionSchema } from "./schemas";

describe("FIRA schemas", () => {
  it("accepts the contract shapes", () => {
    expect(FiraListSchema.safeParse(firaList()).success).toBe(true);
    expect(FiraUploadOutSchema.safeParse(firaUploadOut()).success).toBe(true);
  });

  it("rejects numeric money and unknown statuses", () => {
    const list = firaList();
    const bad = list.items.map((item) => ({
      ...item,
      foreign_amount: { amount: 100, currency: "USD" },
    }));
    expect(FiraListSchema.safeParse({ ...list, items: bad }).success).toBe(false);
    const result = { ...firaUploadOut().result, outcome: "ok" };
    expect(FiraUploadOutSchema.safeParse({ ...firaUploadOut(), result }).success).toBe(false);
  });

  it("requires fira_status on transactions (nullable)", () => {
    const row = { id: "t", fira_status: "lost" };
    expect(TransactionSchema.shape.fira_status.safeParse(row.fira_status).success).toBe(false);
    expect(TransactionSchema.shape.fira_status.safeParse(null).success).toBe(true);
  });
});
