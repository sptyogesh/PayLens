"use client";

import { Button } from "@/components/ui/Button";
import { toApiError } from "@/hooks/useApi";
import { PAY_TEXT } from "@/lib/constants";

import type { PayButtonProps } from "./types";

/** Test mode (NEXT_PUBLIC_PAYPAL_MODE=fake): same backend calls, no PayPal script. */
export function FakeCheckoutButton({ order, createOrder, capture, fail }: PayButtonProps) {
  const pay = async () => {
    if (!order) return;
    try {
      await capture(await createOrder(order));
    } catch (error) {
      fail(toApiError(error).message);
    }
  };
  return (
    <Button disabled={!order} onClick={() => void pay()}>
      {PAY_TEXT.fakeButton}
    </Button>
  );
}
