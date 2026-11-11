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

## Deploy on Render (free plan)

`render.yaml` is a Render Blueprint: one PostgreSQL 18 database (`paylens-db`), the backend
(`paylens-api`) and the frontend (`paylens-web`). In the Render dashboard choose **New → Blueprint**
and pick this repository. Render then asks for the values marked "you enter" below.

### What happens on deploy

- **Tables**: the backend creates any missing tables when it starts (`create_all` at startup), so
  the first deploy and every restart work on an empty database. No migration step is needed.
- **Demo data**: with `SEED_DEMO_ON_STARTUP=true` (set in `render.yaml`) the backend loads the 24
  "Demo seed" payments in a background thread at every start. It is idempotent (rows are keyed by
  their seed id), so restarts never duplicate them. The free plan has no shell, so this replaces
  `uv run python -m scripts.seed_demo`. Set it to `false` to show only real sandbox data.
- **Frontend build**: Next.js bakes every `NEXT_PUBLIC_*` value into the bundle at **build time**.
  `npm run build` first runs `scripts/check-public-env.ts`, which stops the build when one is
  missing or wrong. After changing a `NEXT_PUBLIC_*` value, redeploy `paylens-web` so it is built
  again (a restart is not enough).

### Environment variables

You enter 6 values; everything else is set by `render.yaml`.

| Service     | Variable                       | Value                                                                                     | Secret?                   |
| ----------- | ------------------------------ | ----------------------------------------------------------------------------------------- | ------------------------- |
| paylens-api | `PAYPAL_CLIENT_ID`             | PayPal **sandbox** app client ID                                                          | Not secret, keep private  |
| paylens-api | `PAYPAL_CLIENT_SECRET`         | PayPal sandbox app secret                                                                 | **Secret**                |
| paylens-api | `LLM_API_KEY`                  | Gemini API key (Google AI Studio)                                                         | **Secret**                |
| paylens-api | `FRONTEND_URL`                 | `https://paylens-web.onrender.com` (exact frontend URL, no `/` at the end; used for CORS) | No                        |
| paylens-web | `NEXT_PUBLIC_API_URL`          | `https://paylens-api.onrender.com` (exact backend URL, `https`, no `/` at the end)        | No (public in the bundle) |
| paylens-web | `NEXT_PUBLIC_PAYPAL_CLIENT_ID` | the same sandbox client ID as `PAYPAL_CLIENT_ID`                                          | No (public by design)     |

Set by `render.yaml` (no action): `DATABASE_URL` (from `paylens-db`), `APP_ENV=production`,
`PAYPAL_MODE=http`, `PAYPAL_BASE_URL` (sandbox), `FORWARDED_ALLOW_IPS`, `STARTUP_SYNC_ENABLED`,
`SEED_DEMO_ON_STARTUP`, `FX_MODE`, `FX_API_URL`, `LLM_MODE`, `LLM_PROVIDER=gemini`,
`LLM_MODEL=gemini-3.6-flash`, `LLM_API_URL`, `PYTHON_VERSION`, `NODE_VERSION`,
`NEXT_PUBLIC_PAYPAL_MODE=http`.

Render names services `https://<name>.onrender.com` when the name is free; if it adds a suffix,
copy the real URLs from each service page into `FRONTEND_URL` and `NEXT_PUBLIC_API_URL`, then
redeploy `paylens-web`.

### Free plan limits

- **Sleeping**: free web services stop after about 15 minutes without traffic. The next visit
  starts the backend again, which can take up to a minute. The app shows "Waking up the PayLens
  server…" and keeps loading pages until the backend answers; it does not show an error. Buttons
  that change data (Pay, Sync now, Ask) are never repeated automatically: if one fails while the
  server wakes, press it again.
- **Database**: Render's free PostgreSQL expires after 30 days (check Render's current terms);
  the demo seed reloads automatically on a new database.
