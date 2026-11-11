"use client";

import { useCallback, useState } from "react";

import { apiPost } from "@/lib/api/client";
import type { CaptureOut } from "@/lib/api/schemas";
import { CaptureOutSchema, PayOrderOutSchema } from "@/lib/api/schemas";

import { toApiError } from "@/hooks/useApi";

import type { PayFormValues } from "./payForm";
import { toOrderBody } from "./payForm";

export type PayResultState =
  | { status: "idle" }
  | { status: "processing" }
  | { status: "success"; capture: CaptureOut }
  | { status: "failed"; message: string };

export type PayActions = {
  result: PayResultState;
  createOrder: (order: PayFormValues) => Promise<string>;
  capture: (orderId: string) => Promise<void>;
  fail: (message: string) => void;
};

/** Create the order and capture it through the PayLens backend (FR-032). */
export function usePayOrder(): PayActions {
  const [result, setResult] = useState<PayResultState>({ status: "idle" });

  const createOrder = useCallback(async (order: PayFormValues) => {
    setResult({ status: "processing" });
    const { order_id } = await apiPost("/pay/orders", toOrderBody(order), PayOrderOutSchema);
    return order_id;
  }, []);

  const capture = useCallback(async (orderId: string) => {
    try {
      const data = await apiPost(
        `/pay/orders/${encodeURIComponent(orderId)}/capture`,
        {},
        CaptureOutSchema,
      );
      setResult({ status: "success", capture: data });
    } catch (error) {
      setResult({ status: "failed", message: toApiError(error).message });
    }
  }, []);

  const fail = useCallback((message: string) => {
    setResult({ status: "failed", message });
  }, []);

  return { result, createOrder, capture, fail };
}
