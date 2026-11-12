# PayLens

AI finance copilot for Indian freelancers paid via PayPal: see hidden fees and FX loss, auto-match
FIRAs to payments, and get CA-ready reports.

- **Live demo:** https://paylens-web.onrender.com (PayPal **sandbox** only; the first visit may take
  up to a minute while the free server wakes up)
- **Video:** https://youtu.be/EbHxlny-FMg
- **Built with GitHub Spec Kit and Claude Code.**

## Features

- **PayPal sync**: payments from the PayPal sandbox via the Transaction Search API, on demand and at
  startup; the `/pay` page takes sandbox payments with Orders v2 and the PayPal JS SDK.
- **Leakage dashboard**: the PayPal fee and the FX loss in INR on every payment, totals for this
  month, the last 3 months or all time, and breakdowns by month and by client.
- **Ask your money**: a chat that may only call read-only tools over your data; code checks every
  number in an answer against the tool results, and tax questions get a "confirm with a CA" note.
- **FIRA matching**: upload FIRA PDFs; the AI reads the fields into a strict schema, code validates
  them and a scoring engine matches each FIRA to its payment (matched, needs review or no match).
- **CA report**: a one-click PDF with income, fees, FX loss, FIRA status, data notes and a short AI
  summary that may only use the report's own numbers.

All amounts are computed by tested code with exact decimals; the AI only explains or extracts.

## Tech stack

- **Backend**: FastAPI, Python 3.12 (`mypy --strict`, Pydantic), PostgreSQL 18, SQLAlchemy.
- **Frontend**: Next.js, TypeScript (strict), zod, AG Grid, Tailwind CSS.
- **AI**: Google Gemini (`gemini-3.6-flash`, free tier) behind a single LLM wrapper over HTTP.
- **PayPal**: OAuth, Transaction Search, Orders v2 and the JS SDK v6 (sandbox only).
- **Exchange rates**: ECB reference rates from Frankfurter, cached in the database.
- **Quality**: pytest, Vitest with Testing Library, Playwright (with accessibility checks), CI on
  GitHub Actions.
- **Hosting**: Render free tier (one Blueprint: database, API, web app).
- **Process**: GitHub Spec Kit (specify, plan, tasks, analyze, implement) with Claude Code.

## Run locally

Requirements: Python 3.12 with [uv](https://docs.astral.sh/uv/), Node 24, PostgreSQL 18.

```bash
npm ci && npm ci --prefix frontend && uv sync --directory backend
cp backend/.env.example backend/.env                 # fill in DATABASE_URL, PayPal sandbox, LLM_API_KEY
cp frontend/.env.example frontend/.env.local         # NEXT_PUBLIC_API_URL=http://localhost:8000
(cd backend && uv run python -m scripts.seed_demo)   # optional demo data
(cd backend && uv run uvicorn app.main:app --reload) # http://localhost:8000
(cd frontend && npm run dev)                         # http://localhost:3000
npm run check:all                                    # lint, types, size, all tests
```

## Honest notes

- **Exchange rates**: the "mid-market" rate is the ECB reference rate from
  [Frankfurter](https://frankfurter.dev), used as a proxy for the true mid-market rate.
- **PayPal's rate is simulated**: the sandbox does not apply real conversion rates, so PayLens
  assumes PayPal pays the mid-market rate minus a **3% spread** and labels it
  "Simulated (sandbox)" everywhere it appears. Real PayPal spreads vary.
- **Sandbox and sample data only**: payments come from the PayPal sandbox and a labelled demo seed
  ("Demo seed", fictional clients); FIRAs are generated samples (`sample_data/fira_samples`).
- **Gemini free tier**: Google may use content sent on the free tier to improve its products, so
  only sandbox and sample data are ever sent. Never upload real FIRAs or financial data here.
- **Gemini rate limits**: uploading many FIRAs at once can hit the free-tier limit; those files show
  "The AI is busy, try again shortly" and are not saved. Upload them again a minute later.
- **Render free tier**: the backend sleeps after about 15 minutes idle; the next visit shows
  "Waking up the PayLens server…" for up to a minute, then loads normally.
- **Not tax advice**: reports and answers are prepared from your data; confirm with a CA.

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
| paylens-web | `NEXT_PUBLIC_API_URL`          | exact backend URL, e.g. `https://paylens-api-9k03.onrender.com` (`https`, no `/` at end)  | No (public in the bundle) |
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
