# PayLens
AI finance copilot for Indian freelancers paid via PayPal. See hidden fees and FX loss, auto-match FIRA documents, and get CA-ready reports.

## AI provider

PayLens calls one LLM through a single wrapper: Google Gemini (free tier, default model
`gemini-3.6-flash`) or Anthropic Claude. Set `LLM_API_KEY` in `backend/.env`; the provider is
detected from the key, or set `LLM_PROVIDER`. A key that belongs to a different provider than
`LLM_PROVIDER` stops the backend at startup, so a key is never sent to the wrong company.

**Free tier and your data:** on the Gemini API free tier, Google may use the content you send to
improve its products ([pricing page](https://ai.google.dev/gemini-api/docs/pricing), "Used to improve
our products: Yes"). PayLens therefore sends only PayPal **sandbox** data, the demo seed and the
generated sample FIRAs. Do not upload real FIRAs or real financial data while on the free tier.
