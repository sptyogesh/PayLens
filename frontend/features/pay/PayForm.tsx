"use client";

import { useState } from "react";

import { FIELD_CLASS, TextField } from "@/components/ui/TextField";
import { CHECKOUT_CURRENCIES, CHECKOUT_DESCRIPTION_MAX, PAY_TEXT } from "@/lib/constants";

import type { PayFormErrors, PayFormValues } from "./payForm";

export type PayFormProps = {
  values: PayFormValues;
  errors: PayFormErrors;
  onChange: (values: PayFormValues) => void;
};

type Field = keyof PayFormValues;

/** Child of PayView: amount, currency and description. Errors show once a field is touched. */
export function PayForm({ values, errors, onChange }: PayFormProps) {
  const [touched, setTouched] = useState<Partial<Record<Field, boolean>>>({});
  const update = (field: Field) => (value: string) => {
    setTouched((current) => ({ ...current, [field]: true }));
    onChange({ ...values, [field]: value });
  };
  const errorFor = (field: Field) => (touched[field] ? errors[field] : undefined);

  return (
    <div className="grid gap-4 sm:grid-cols-3">
      <TextField
        label={PAY_TEXT.amountLabel}
        inputMode="decimal"
        value={values.amount}
        error={errorFor("amount")}
        onValueChange={update("amount")}
      />
      <CurrencySelect value={values.currency} onValueChange={update("currency")} />
      <TextField
        label={PAY_TEXT.descriptionLabel}
        className="sm:col-span-3"
        maxLength={CHECKOUT_DESCRIPTION_MAX + 1}
        value={values.description}
        error={errorFor("description")}
        onValueChange={update("description")}
      />
    </div>
  );
}

function CurrencySelect({
  value,
  onValueChange,
}: {
  value: string;
  onValueChange: (v: string) => void;
}) {
  return (
    <label className="text-sm font-medium">
      {PAY_TEXT.currencyLabel}
      <select
        className={FIELD_CLASS}
        value={value}
        onChange={(event) => {
          onValueChange(event.target.value);
        }}
      >
        {CHECKOUT_CURRENCIES.map((currency) => (
          <option key={currency}>{currency}</option>
        ))}
      </select>
    </label>
  );
}
