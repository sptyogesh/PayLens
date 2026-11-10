"use client";

/**
 * Parent for /pay. Children: PayForm (inputs), PayButton (PayPal or test-mode button)
 * and PayResult (confirmation or error). Calls go through usePayOrder to the backend.
 */
import { useState } from "react";

import { PageHeader } from "@/components/layout/PageHeader";
import { Card } from "@/components/ui/Card";
import { Disclaimer } from "@/components/ui/Disclaimer";
import { PAY_TEXT } from "@/lib/constants";

import { PayButton } from "./PayButton";
import { PayForm } from "./PayForm";
import type { PayFormValues } from "./payForm";
import { EMPTY_FORM, validatePayForm } from "./payForm";
import { PayResult } from "./PayResult";
import { usePayOrder } from "./usePayOrder";

export function PayView() {
  const [values, setValues] = useState<PayFormValues>(EMPTY_FORM);
  const { order, errors } = validatePayForm(values);
  const pay = usePayOrder();
  return (
    <>
      <PageHeader title={PAY_TEXT.title} />
      <div className="space-y-6">
        <Disclaimer kind="sandboxCheckout" />
        <Card title={PAY_TEXT.formTitle}>
          <div className="space-y-4">
            <PayForm values={values} errors={errors} onChange={setValues} />
            <PayButton
              order={order}
              createOrder={pay.createOrder}
              capture={pay.capture}
              fail={pay.fail}
            />
          </div>
        </Card>
        <PayResult result={pay.result} />
      </div>
    </>
  );
}
