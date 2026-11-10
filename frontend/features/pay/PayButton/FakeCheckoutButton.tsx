"use client";

import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { toApiError } from "@/hooks/useApi";
import { PAY_TEXT } from "@/lib/constants";

import type { PayButtonProps } from "./types";

/**
 * Test mode (NEXT_PUBLIC_PAYPAL_MODE=fake): same backend calls, no PayPal script.
 * Disabled while a payment is processing, so a double click cannot create two orders.
 */
export function FakeCheckoutButton({ order, createOrder, capture, fail }: PayButtonProps) {
  const [isPending, setIsPending] = useState(false);
  const pay = async () => {
    if (!order || isPending) return;
    setIsPending(true);
    try {
      await capture(await createOrder(order));
    } catch (error) {
      fail(toApiError(error).message);
    } finally {
      setIsPending(false);
    }
  };
  return (
    <Button disabled={!order || isPending} onClick={() => void pay()}>
      {PAY_TEXT.fakeButton}
    </Button>
  );
}
