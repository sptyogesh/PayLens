# PayLens — Devpost submission

**Live demo:** https://paylens-web.onrender.com (PayPal sandbox; first load may take up to a minute
while the free server wakes up) · **Video:** https://youtu.be/EbHxlny-FMg ·
**Built with GitHub Spec Kit and Claude Code.**

## Inspiration

Indian freelancers paid by foreign clients through PayPal rarely know how much they actually lose
per payment. The PayPal fee is visible, but the currency conversion is not: the rate PayPal applies
sits below the mid-market rate, and that gap quietly takes a few percent of every invoice. At tax
time the same freelancers chase FIRAs (Foreign Inward Remittance Advice) to prove export
income, and hand their CA a pile of statements to reconcile by hand. We wanted one place that shows
the real cost of getting paid and prepares the paperwork.

## What it does

- **Syncs PayPal payments** from the PayPal sandbox with the Transaction Search API, on demand and
  at startup, and records new payments taken on the `/pay` page (Orders v2 with the PayPal JS SDK).
- **Shows the leakage on every payment**: the PayPal fee and the FX loss in INR, against a
  mid-market rate. A dashboard totals them for this month, the last 3 months or all time, with
  breakdowns by month and by client.
- **Answers questions about your money** ("How much FX loss did I have this quarter?"). The AI may
  only call read-only tools over your data, and code checks every number in the answer against the
  tool results; an answer with a number that did not come from your data is replaced. Every answer
  shows the figures it is based on, and tax questions get a "confirm with a CA" note.
- **Matches FIRAs to payments**: upload FIRA PDFs, the AI reads the fields into a strict schema,
  code validates them and a scoring engine matches each FIRA to its payment (matched, needs review
  or no match). Payments still missing a FIRA are listed.
- **Creates a CA-ready PDF report** in one click: income, fees, FX loss, FIRA status, data notes and
  a short AI summary that may only use the report's own numbers.

Everything runs on PayPal sandbox and clearly labelled demo data.

## How we built it

- **Spec first**: each feature went through the GitHub Spec Kit cycle (specify, plan, tasks,
  analyze, implement) against a written project constitution, with Claude Code as the coding agent
  working under those rules.
- **Backend**: FastAPI and Python with strict typing (`mypy --strict`, Pydantic at every boundary)
  and PostgreSQL. All money uses exact decimals, never floats.
- **Frontend**: Next.js and TypeScript (strict), zod-validated API data, AG Grid for the
  transaction tables.
- **AI**: Google Gemini (`gemini-3.6-flash`, free tier) behind a single LLM wrapper, called over
  plain HTTP. Code computes every number; the AI only explains or extracts.
- **PayPal**: OAuth client credentials, Transaction Search for history, Orders v2 plus the JS SDK
  v6 for checkout, sandbox only.
- **Exchange rates**: ECB reference rates from Frankfurter as a mid-market proxy, cached in the
  database.
- **Quality**: 735 backend tests, 199 frontend unit tests and 63 Playwright end-to-end tests,
  including accessibility checks and a full journey from payment to CA report, run in CI on every
  push. Fake PayPal, FX and LLM gateways keep tests away from real services.
- **Hosting**: Render free tier from one Blueprint (PostgreSQL, API and web app).

## Challenges we ran into

- **No real conversion in the sandbox**: PayPal's sandbox does not apply real exchange rates, so we
  simulate PayPal's rate as mid-market minus a 3% spread and label it "Simulated (sandbox)"
  everywhere it appears.
- **Keeping the AI honest about numbers**: our first grounding check could be fooled, for example
  by digits inside a client name, rounded figures or a sign flip. We rewrote it to accept only exact
  numbers from numeric tool fields, and added tests for each bypass.
- **Exact totals**: summing per-payment losses and rounding the total gave cards that were a paisa
  off. Totals are now the sum of rounded parts, so every displayed identity adds up exactly.
- **Switching AI provider mid-build**: with no budget, we moved to the Gemini free tier. That meant
  a translating adapter (function calling with call ids and thought signatures, PDF input, JSON
  output) and a startup check so an API key is never sent to the wrong company. The newest Flash
  model was overloaded during our real-AI check, so we chose the stable previous one.
- **A rupee sign in the PDF**: the built-in PDF fonts cannot draw "₹", so the report embeds an
  open-licence font just for that glyph.
- **Free hosting realities**: the backend sleeps when idle, build-time `NEXT_PUBLIC_*` variables and
  a CORS mismatch after deploy. We added a "waking up" state with safe retries, a build guard that
  stops a frontend build with a missing value, and a deploy guide.
- **CI outages**: a DNS outage on GitHub's runners broke the browser install, so the step now falls
  back to installing the browser alone.

## Accomplishments that we're proud of

- The chat answer and the dashboard agree to the paisa; the AI never introduces its own numbers.
- A FIRA from the sample set is read and matched end to end by a real Gemini call, with every field
  correct.
- One honest, labelled demo: sandbox data, a simulated rate that says so, and "not tax advice"
  wherever money meets tax.
- A full test suite and CI from day one, including an end-to-end journey across all five features.

## What we learned

- Writing the spec and constitution first made a fast AI-assisted build safer: the agent had clear
  limits (file sizes, no magic numbers, tests with every task, no git actions without approval).
- "Code computes, AI explains" is the right split for finance: grounding checks and code-written
  fallbacks matter more than prompt wording.
- Sandbox APIs differ from production in ways that matter (conversion, data delays), and being
  explicit about it in the UI builds more trust than hiding it.
- Free tiers work for a demo if you design for their limits: cold starts, rate limits and data-use
  terms.

## What's next

These are plans, not features in the current build:

- PayPal live mode with the user's consent, using real conversion details instead of a simulated
  spread.
- Reading bank FIRA e-mails or statements directly instead of PDF uploads.
- Exports in the formats CAs use for ITR and GST filings.
- Alerts when a payment's leakage is unusually high, and tips on cheaper ways to receive money.
- A paid AI tier so real (non-sample) documents can be processed without free-tier data use.

## Built with

PayPal Orders v2 · PayPal Transaction Search · PayPal JS SDK · Google Gemini · FastAPI · Next.js ·
PostgreSQL · AG Grid · Render · GitHub Spec Kit · Claude Code
