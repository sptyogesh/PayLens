"use client";

import { PayPalOneTimePaymentButton, PayPalProvider } from "@paypal/react-paypal-js/sdk-v6";

import { PAY_TEXT } from "@/lib/constants";

import type { PayButtonProps } from "./types";

/**
 * PayPal JS SDK v6 checkout (research R7). The order (and its currency) is created on the
 * PayLens backend, so the SDK is loaded once with the public sandbox client ID only.
 */
export function PayPalCheckoutButton({ order, createOrder, capture, fail }: PayButtonProps) {
  return (
    <PayPalProvider
      clientId={process.env.NEXT_PUBLIC_PAYPAL_CLIENT_ID ?? ""}
      environment="sandbox"
      components={["paypal-payments"]}
      pageType="checkout"
    >
      <PayPalOneTimePaymentButton
        disabled={!order}
        createOrder={async () => {
          if (!order) throw new Error(PAY_TEXT.noPayment);
          return { orderId: await createOrder(order) };
        }}
        onApprove={({ orderId }) => capture(orderId)}
        onCancel={() => {
          fail(PAY_TEXT.noPayment);
        }}
        onError={() => {
          fail(PAY_TEXT.noPayment);
        }}
      />
    </PayPalProvider>
  );
}
