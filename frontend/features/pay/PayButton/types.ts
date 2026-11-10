import type { PayFormValues } from "../payForm";

export type PayButtonProps = {
  /** The valid order, or null while the form is invalid (the button is then disabled). */
  order: PayFormValues | null;
  createOrder: (order: PayFormValues) => Promise<string>;
  capture: (orderId: string) => Promise<void>;
  fail: (message: string) => void;
};
