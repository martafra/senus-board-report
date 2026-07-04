# Senus PLC — AI-Native Board Report Platform

An AI-native platform that turns Senus PLC's real, publicly filed financial disclosures into an
interactive Board Report for Management, the Board, Equity Investors and Credit Providers.

> Status: work in progress, built incrementally. This README is updated as each phase lands.

## Why this exists

Senus PLC is an Irish Natural Capital management software company that listed on Euronext Access
Dublin in December 2025. This project was built for the Assiduous Technology Graduate Assessment: design
and build a full-stack, AI-native Board Report application using Senus's real historic financials.

## Data source and honesty about provenance

All financial figures originate from the **Senus PLC Information Document** (the Euronext listing
prospectus, December 2025) — the fullest real financial disclosure publicly available for the company,
covering FY2024 and FY2025 (years ended 30 June). A copy is kept at
[`data/source_documents/`](data/source_documents/).

The source document does **not** include a monthly/quarterly breakdown, an explicit EBITDA/D&A line, a
detailed balance sheet, or interest expense — normal for a two-year summary in a listing document. Rather
than inventing false precision, every financial fact in this platform is tagged with a **provenance**:

- `REPORTED` — taken verbatim from the Information Document.
- `MODELLED` — derived under an explicit, disclosed assumption (e.g. a seasonality-based monthly split of
  the two real annual actuals, or an EBITDA margin computed assuming near-zero D&A for this asset-light
  software business).

The UI badges every chart/figure accordingly, and assumptions are documented in full further down this
README as each metric is built.

## Architecture

```
assiduous/
  apps/api/     FastAPI backend (Python) — data model, metrics engine, AI extraction & insights
  apps/web/     React (Vite + TypeScript) frontend — the Board Report UI
  data/source_documents/   Source filings (e.g. the Information Document PDF)
  data/extracted/          AI-extracted structured JSON, reviewed before being loaded into Postgres
  docker-compose.yml        Local Postgres + API
```

- **Backend**: FastAPI + SQLAlchemy 2.0 (async) + Alembic + Pydantic v2, PostgreSQL.
- **Frontend**: React (Vite) + TypeScript + Tailwind CSS, talking to the backend over REST.
- **AI**: Anthropic Claude API, used for (1) extracting structured financial data from source PDFs into
  the database, and (2) generating board-ready narrative commentary from computed metrics.

## Running locally

1. Copy env files: `cp .env.example .env` and `cp apps/web/.env.example apps/web/.env`. Fill in
   `ANTHROPIC_API_KEY` in `.env` (required once the AI extraction/insights phases land).
2. Start Postgres + API: `docker compose up --build`.
3. Start the frontend: `cd apps/web && npm install && npm run dev` (served at `http://localhost:5173`).
4. Backend health check: `http://localhost:8000/health`. Interactive API docs: `http://localhost:8000/docs`.

## AI-assisted development workflow

This project was built collaboratively with Claude (Anthropic), used for: researching Senus's real
public disclosures, architecture planning, and writing the application code across backend, frontend and
the AI extraction/insights pipelines. Design decisions, assumptions and validation steps are documented
in this README as the project progresses.

## Status / roadmap

- [x] Repo scaffolding, Docker Compose, base FastAPI + React apps
- [ ] Data model (SQLAlchemy models + Alembic migration)
- [ ] AI extraction pipeline (Claude PDF → structured JSON → Postgres)
- [ ] FastAPI backend (auth, metrics endpoints)
- [ ] React frontend (dashboard, charts per Board Report section)
- [ ] AI-generated insights/commentary
- [ ] Validation pass, deployment, demo video
