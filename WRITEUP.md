# Senus PLC Board Report: One-Page Summary

An AI-native platform that turns Senus PLC's real, publicly filed financial disclosures into an
interactive Board Report for Management, the Board, Equity Investors and Credit Providers.

## The problem

Senus PLC is an Irish Natural Capital software company, listed on Euronext Access Dublin in
December 2025. Its public filings (a listing prospectus, half-year results, an audited annual
report) contain everything a board needs to judge performance, but scattered across several
documents, in accountant-facing language, with no single interactive view. The brief asked for a
platform that turns that raw disclosure into a Board Report covering Growth & Revenue,
Profitability, Cash & Liquidity, Solvency & Leverage and Returns, with AI-powered insight, built
using real historic data rather than a synthetic dataset.

## Key decisions

**Provenance over invented precision.** Senus's filings give two annual data points and no
monthly breakdown, no EBITDA line, and a two-year balance sheet. Rather than fabricate the missing
detail, every stored fact is tagged `REPORTED` (verbatim from a filing) or `MODELLED` (derived
under a disclosed assumption, e.g. splitting an annual total into months), and the UI badges every
figure accordingly. Where two documents disagree on a number, the discrepancy is logged and shown,
never silently resolved by picking one.

**An EAV fact table, not fixed columns.** Financial facts arrive incrementally from independent
documents with heterogeneous, mixed-provenance metrics. `financial_facts(period_id, metric_key,
value, provenance, source_doc_id)` fits that shape; a fixed-column schema would fight it. Loading
is additive: a fact already in the database is never overwritten by a later document restating it,
a genuine conflict is logged for manual review instead.

**Python end to end, chosen for the CV.** FastAPI + SQLAlchemy 2.0 (async) + Alembic + Postgres on
the backend, React + Vite + TypeScript on the frontend, talking over REST. Google Gemini
(`gemini-2.5-flash`, free tier) does two distinct jobs: extracting structured facts from source
PDFs into review-ready JSON before it ever reaches the database, and generating cached, regenerable
board commentary from the already-computed metrics, in plain language a non-financial reader can
follow.

## How the outputs were validated

Every AI extraction is written to a JSON file and manually checked against the source PDF text
before being loaded, not trusted blind. This caught real errors early: a balance sheet's aggregate
"Debtors" line mislabelled as a note-level sub-component, a cash flow subtotal picked from the
wrong line, sign-convention mismatches on P&L expense lines. Each one was fixed both in the data
and in the extraction prompt, so later documents didn't repeat it. Backend logic (60 tests) and
frontend behaviour (37 tests) are covered by automated tests using synthetic data, so a formula
regression is caught even when the real dataset wouldn't currently expose it; the AI's own output
quality is a human-review process instead, since correctness there isn't something a unit test can
judge.

Two real production bugs, found by manually exercising a live Docker deployment rather than by any
test: an async transaction held open across a slow Gemini call exhausted the connection pool and
hung unrelated endpoints (fixed by committing before the call and running it via
`asyncio.to_thread`); and, once deployed, Google was found to block direct Gemini calls from most
cloud-hosting datacenter IP ranges, including Render's, a hard platform constraint with no key or
project setting that fixes it. The fix was a small serverless proxy on Vercel that makes the same
call from a network Google doesn't block, with the API key still only ever held server-side.

## AI-assisted development workflow

The application was built collaboratively with Claude Code, used for architecture planning and
writing the code across backend, frontend, and the extraction/insights pipelines, incrementally and
with review at each phase. That is separate from the app's own runtime AI (Gemini), which powers
extraction and insights once the app is running, chosen independently for its free tier.

## Links

- GitHub: https://github.com/martafra/senus-board-report
- Live app: https://senus-board-report-silk.vercel.app
- Demo video: https://youtu.be/MNgS4Oo0RPk
