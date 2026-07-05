# Senus PLC: AI-Native Board Report Platform

An AI-native platform that turns Senus PLC's real, publicly filed financial disclosures into an
interactive Board Report for Management, the Board, Equity Investors and Credit Providers.

> Status: work in progress, built incrementally. This README is updated as each phase lands.

## Data Source

All financial figures originate from Senus PLC's real, public disclosures. Copies of every source
document are kept at [`data/source_documents/`](data/source_documents/):

| Document | Date | What it's used for |
| --- | --- | --- |
| `Senus_PLC_Information_Document_2025-12.pdf` | Dec 2025 | Euronext listing prospectus. Primary source for FY2024/FY2025 annual P&L, balance sheet, cash flow, customer/KPI metrics. **Ingested.** |
| `Senus_HalfYearResults_HY2026_2026-03-19.pdf` | 19 Mar 2026 | Unaudited half-year results, 6 months to 31 Dec 2025 (HY2026), with a REPORTED comparative for 6 months to 31 Dec 2024 (HY2025). **Ingested** as two HALF_YEAR periods. |
| `ADF_Farm_Solutions_Audited_Financial_Statements_2025-06-30.pdf` | FY ended 30 Jun 2025 | Full **audited** statutory annual report for Senus (formerly ADF Farm Solutions Ltd). Richer note-level detail than the Information Document (debtors/creditors breakdown, headcount, R&D spend, director remuneration, loan repayment schedule). **Ingested**, merged additively into the existing FY2024/FY2025 periods. |
| `Senus_Limited_Balance_Sheet_2025-12-08.pdf` | 8 Dec 2025 | Pre-listing re-registration balance sheet (company re-registering as a PLC). Context only, not ingested. |
| `Senus_PLC_Memo_and_Articles_of_Association_2025-12.pdf` | Dec 2025 | Constitutional document. Confirms share capital structure (€1,000,000 / 100,000,000 ordinary shares @ €0.01). Not a financial-facts source. |
| `Senus_Notice_of_AGM_2026.pdf` / `Senus_Form_of_Proxy_AGM_2026.pdf` | 2026 AGM (8 Jul 2026) | Governance/voting context (director re-election, auditor continuation, pre-emption disapplication). Not a financial-facts source. |
| `Senus_PLC_Direct_Listing_Launch_PR_2025-12-18.pdf` | 18 Dec 2025 | Confirms admission price (€5.126) and market cap at admission (€13.13m). Candidate one-off facts for a Returns/valuation view; not yet ingested. |
| `Senus_Notification_of_Results_HY2026_2026-02-17.pdf` / `Senus_PR_Notice_of_AGM_2026-06-05.pdf` | Feb/Jun 2026 | Calendar announcements only, no new figures. |
| `Senus_PR_Leadership_Transition_2026-06-24.pdf` | 24 Jun 2026 | MD Brendan Allen moving to Vice Chairman by Oct 2026; FY2026 annual results due 11 Sep 2026. Narrative context only. |
| `Senus_Corporate_Presentation_2026-03-19.pdf` | Mar 2026 | Investor pitch deck. Confirms figures already in the Information Document; adds narrative context (company history, team, named customers) but no new financial facts. |

Known discrepancy, not yet reconciled: the audited FY2025 accounts' post-balance-sheet note states the
Oct 2025 pre-listing capital raise was €830,000, while several press releases describe the same round
(or a related one) as "€1.1m". Recorded here rather than silently resolved with an invented number.

## Data pipeline design notes

- **Extraction is additive, never destructive.** Every document is extracted independently (`python
  scripts/ingest.py extract --doc <key>`), written to a reviewable JSON file under `data/extracted/`,
  manually checked against the source text, then loaded (`load <path>`). Loading upserts by
  `(period, metric_key)`: a fact already in the database is never silently overwritten or deleted by a
  later document restating it (every Senus press release repeats the same "FY2025 revenue €836,991"
  boilerplate, for instance). A genuinely conflicting value between two documents is printed for manual
  review instead. This matters because we now ingest multiple overlapping documents (the Information
  Document, the HY2026 results, the audited annual report) covering some of the same periods.
- **Sign conventions**, kept consistent across every document's extraction so periods stay comparable:
  profit/loss subtotals (`gross_profit`, `operating_profit`, `profit_before_tax`, `profit_after_tax`) are
  negative for a loss; P&L expense lines (`cost_of_sales`, `admin_expenses`, `distribution_costs`,
  `interest_expense`) are positive magnitudes; cash flow totals and their components are signed by actual
  direction (negative = outflow); `tax_expense` is positive when it's a net credit added to
  `profit_before_tax` to reach `profit_after_tax` (this company's R&D credits currently exceed its tax
  charge). A balance-sheet face total (`debtors`, `creditors_current`) is kept distinct from a note-level
  sub-component of the same name's cousin (`trade_debtors`, `trade_creditors`); they are different
  real-world numbers and must never share a metric_key.
- **Monthly figures are always MODELLED**, never treated as reported: `scripts/ingest.py model-monthly`
  splits each REPORTED annual total evenly across 12 months. Where a REPORTED half-year actual exists for
  that fiscal year (FY2025, from the HY2026 release), the first six months use that real total instead of
  an assumed percentage, and the second six months are the annual total minus that real H1 actual. Where
  no REPORTED half-year exists yet (FY2024), the split falls back to the H1 share actually measured from
  a fiscal year that does have one (currently 40.7%), rather than a fixed guess.
- Every extraction is human-reviewed against the source PDF text before loading; the first HY2026
  extraction attempt had labelling errors (e.g. a balance sheet's aggregate "Debtors" line mislabelled as
  the note-level "trade debtors" sub-component, and the wrong cash flow subtotal picked for
  `cash_operating`) that were caught this way and fixed both in that data and in the extraction prompt
  (`app/ai/extraction.py`) so later documents didn't repeat them.

## Architecture

```
assiduous/
  apps/api/     FastAPI backend (Python): data model, metrics engine, AI extraction & insights
  apps/web/     React (Vite + TypeScript) frontend: the Board Report UI
  data/source_documents/   Source filings (e.g. the Information Document PDF)
  data/extracted/          AI-extracted structured JSON, reviewed before being loaded into Postgres
  docker-compose.yml        Local Postgres + API
```

- **Backend**: FastAPI + SQLAlchemy 2.0 (async) + Alembic + Pydantic v2, PostgreSQL.
- **Frontend**: React (Vite) + TypeScript + Tailwind CSS, talking to the backend over REST.
- **AI**: Google Gemini API (free tier), used for (1) extracting structured financial data from source
  PDFs into the database, and (2) generating board-ready narrative commentary from computed metrics.

## Running locally

1. Copy env files: `cp .env.example .env` and `cp apps/web/.env.example apps/web/.env`. Fill in
   `GEMINI_API_KEY` in `.env` (a free key from aistudio.google.com; required for the AI extraction
   pipeline and, later, AI insights).
2. Start Postgres + API: `docker compose up --build`. Apply migrations once the containers are up:
   `docker compose exec api alembic upgrade head`.
3. Start the frontend: `cd apps/web && npm install && npm run dev` (served at `http://localhost:5173`).
4. Backend health check: `http://localhost:8000/health`. Interactive API docs: `http://localhost:8000/docs`.
5. Run the data pipeline (either inside the container, `docker compose exec api ...`, or locally from
   `apps/api` with the venv active; both resolve `data/` correctly):
   ```
   python scripts/ingest.py extract --doc information_document --dry-run   # preview only
   python scripts/ingest.py extract --doc information_document             # writes data/extracted/*.json
   # review the JSON against the source PDF, then:
   python scripts/ingest.py load data/extracted/senus_information_document.json
   python scripts/ingest.py model-monthly   # derive MODELLED monthly splits from REPORTED periods
   ```
   Repeat `extract`/`load` for the other registered documents (`--doc hy2026_results`,
   `--doc adf_audited_fy2025`; see `DOCUMENTS` in `scripts/ingest.py` for the full registry).

## Backend API

Once the pipeline above has loaded data, the API serves it as computed board metrics (see
`app/services/metrics.py` for the formulas and the assumptions behind each one):

- `POST /auth/login`, `GET /auth/me`: JWT login for the seeded demo user (`scripts/seed_user.py`).
- `GET /metrics/growth`: revenue, YoY growth (any period type, vs. the same period a year earlier),
  MoM growth (MONTHLY only), customer counts by channel, bookings.
- `GET /metrics/profitability`: gross/operating/EBITDA margin, plus a cost breakdown
  (`cost_of_sales`, `admin_expenses`, `distribution_costs`, each shown only for periods that
  disclose it). EBITDA = `operating_profit + depreciation`, both REPORTED facts, so no assumed D&A
  figure is needed for periods loaded so far.
- `GET /metrics/cash-liquidity`: an EBITDA-to-Free-Cash-Flow bridge (`ebitda`,
  `operating_cash_adjustments` = `cash_operating - ebitda`, `cash_investing`, `free_cash_flow` =
  `cash_operating + cash_investing`; the four sum together consistently, so the frontend charts the
  walk from one to the other as a waterfall rather than showing two disconnected numbers), cash
  runway in months (only shown while actually burning cash), working capital.
- `GET /metrics/solvency`: Debt Service Coverage Ratio. ANNUAL periods only: half-year releases
  haven't disclosed the loan repayment schedule this needs, so it isn't approximated at that
  granularity, it's simply not shown.
- `GET /metrics/returns`: Return on Capital Employed (`operating_profit / (Total Assets - Current
  Liabilities)`), using period-end balances built from the disclosed asset facts.
- `GET /targets/kpi`: Senus's own disclosed 2030 strategic targets (Revenue CAGR, EBITDA-positive
  date, Enterprise customer count, Enterprise ACV, Ireland revenue share), ordered by target date.
  Shown on the Growth & Revenue page so actual performance can be judged against the company's own
  stated goals, not just against last year.
- `GET /targets/debt`: the company's disclosed debt instruments (name, principal, provider, drawn
  date), each flagged Outstanding or Repaid. Two director working-capital loans were repaid in
  October 2025 (exact day not disclosed by the source document, so dated to the last day of that
  month, noted as such); shown on the Solvency & Leverage page alongside DSCR so a repaid loan
  doesn't read as if it's still part of the company's debt burden.

Every metric response includes a plain-language `description` (meant for a UI tooltip) and every
period carries `is_actual_reported` (REPORTED vs MODELLED), so the frontend can badge each figure
without duplicating that knowledge.

### AI insights

- `GET /insights/{section}`, `POST /insights/{section}/regenerate` (section is one of the five
  metrics keys above): a short board commentary generated from that section's already-computed
  metrics (never raw facts), cached in `ai_insights` until explicitly regenerated. The prompt
  (`app/ai/insights.py`) requires plain language (any financial term explained in the same
  sentence) and requires the model to flag when it's discussing a MODELLED figure rather than a
  REPORTED one.
- The Gemini call is synchronous/blocking, so it's run via `asyncio.to_thread` and the DB
  transaction is committed *before* that call starts (`app/services/insights.py`). This was fixed
  after a real bug found in manual testing: holding the transaction open across the Gemini call
  left the connection "idle in transaction" for as long as that call took, and with the connection
  pool that small, a couple of overlapping requests exhausted it, hanging even unrelated endpoints
  like `/auth/login` (verified via `pg_stat_activity`, then reproduced and fixed).
- The Gemini free tier is rate-limited (20 requests/day for `gemini-2.5-flash` at the time of
  writing); a failure there returns a clean `503` with a message, rather than a bare `500`.

## Frontend

React (Vite) SPA at `apps/web`. A landing page at `/` introduces the platform and opens sign-in in
a Dialog (JWT stored in `localStorage`) without navigating away; once authenticated it redirects to
`/dashboard`, a shell with one page per Board Report section (Growth & Revenue, Profitability,
Cash & Liquidity, Solvency & Leverage, Returns), each identified by a fixed accent color reused
consistently for that section's nav item, heading dot and chart series.

Each section page shows:
- An `InsightPanel`: the AI commentary, a Regenerate button, and a "Generated on \<date\>" caption
  with the model name tucked behind a hover/focus info tooltip rather than shown inline, so the
  caption reads cleanly while the detail is still one interaction away.
- A chart in that section's accent color.
- A `MetricsTable` with a Reported/Modelled badge per period, a hover/focus-accessible info tooltip
  per metric column explaining what it means, and the same tooltip pattern on any blank cell
  explaining why that figure wasn't disclosed for that period, rather than leaving an unexplained
  dash.

The Growth & Revenue page additionally shows a `KPITargetsPanel` (Senus's disclosed 2030 targets),
and the Solvency & Leverage page a `DebtInstrumentsPanel` (the company's disclosed debt, each
badged Outstanding or Repaid, with the repayment date behind an info tooltip for any that are).
The Cash & Liquidity page additionally shows an `EbitdaToFcfBridge`: a small waterfall chart for
the most recent period with complete data, walking from EBITDA through the working-capital/
interest/tax adjustment and investing cash flow to Free Cash Flow, so the connection between the
two headline figures is a reconciliation a reader can see, not just two numbers side by side.

Data fetching goes through TanStack Query calling the API above.

```
cd apps/web
cp .env.example .env   # points at the API, defaults to http://localhost:8000
npm install
npm run dev             # http://localhost:5173
```

## Testing

**Backend** (`apps/api/tests/`): the deterministic, non-AI logic. `_load`'s additive/conflict-safe
upserting, `_model_monthly`'s REPORTED-half-year-aware split, the extraction Pydantic schemas, JWT
auth, and every `/metrics/*` calculation (against synthetic data, not the real dataset, so a formula
change is caught even if the real numbers wouldn't currently expose it). Deliberately does **not**
call the real Gemini API (slow, non-deterministic, costs quota); AI extraction quality is instead
validated the way it's described above, by a human reviewing each extraction's JSON against the
source PDF before loading.

```
cd apps/api
docker compose exec db psql -U senus -d senus_board_report -c "CREATE DATABASE senus_board_report_test;"  # once
source .venv/bin/activate
pytest
```

**Frontend** (`apps/web/src/**/*.test.{ts,tsx}`): the API client, the auth context (login/logout/
token persistence), formatting helpers, and the Profitability page's loading/error/data states
(Vitest + React Testing Library, with the API mocked so tests don't need a running backend).

```
cd apps/web
npm test
```

## Deployment

See [`DEPLOYMENT.md`](DEPLOYMENT.md): API + Postgres on Render, frontend on Vercel. The API
container is self-seeding (migrates, seeds the demo user, and loads all three source documents on
every boot), so a first deploy needs no manual database step.

## AI-assisted development workflow

This project was built collaboratively with Claude Code (Anthropic), used for: researching Senus's real
public disclosures, architecture planning, and writing the application code across backend, frontend and
the AI extraction/insights pipelines. That's separate from the app's own runtime AI (Google Gemini,
chosen for its free tier), which powers the extraction and insights features once the app is running.
Design decisions, assumptions and validation steps are documented in this README as the project
progresses.
