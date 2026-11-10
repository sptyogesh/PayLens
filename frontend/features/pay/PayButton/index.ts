import { FakeCheckoutButton } from "./FakeCheckoutButton";
import { PayPalCheckoutButton } from "./PayPalCheckoutButton";

export type { PayButtonProps } from "./types";

/** Real PayPal button, or the test-mode button when NEXT_PUBLIC_PAYPAL_MODE=fake (E2E). */
export const PayButton =
  process.env.NEXT_PUBLIC_PAYPAL_MODE === "fake" ? FakeCheckoutButton : PayPalCheckoutButton;
