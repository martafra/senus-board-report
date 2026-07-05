"""CLI to run the Senus PLC data pipeline: PDF -> AI extraction -> Postgres.

Usage (from apps/api, with the venv active):
    python scripts/ingest.py extract [--doc information_document|hy2026_results] [--dry-run]
    python scripts/ingest.py load <json_path>
    python scripts/ingest.py model-monthly
"""
import argparse
import asyncio
import json
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import delete, select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.ai.extraction import extract_from_pdf  # noqa: E402
from app.core.db import AsyncSessionLocal  # noqa: E402
from app.models import (  # noqa: E402
    CustomerChannel,
    CustomerMetric,
    DebtInstrument,
    FinancialFact,
    FinancialPeriod,
    KPITarget,
    PeriodType,
    Provenance,
    SourceDocument,
)
from app.schemas.extraction import ExtractionResult  # noqa: E402


def _find_data_dir() -> Path:
    """Locate the repo's data/ directory. Inside Docker, docker-compose mounts it directly at
    /data and sets DATA_DIR=/data (see docker-compose.yml); locally (venv), it's found relative to
    this file's own location (apps/api/scripts/ingest.py -> scripts -> api -> apps -> repo root)."""
    env_override = os.environ.get("DATA_DIR")
    if env_override:
        return Path(env_override)
    here = Path(__file__).resolve()
    try:
        return here.parents[3] / "data"
    except IndexError:
        raise RuntimeError(
            "Can't locate the data/ directory (not running from the repo checkout and DATA_DIR "
            "isn't set). Set the DATA_DIR environment variable explicitly."
        )


DATA_DIR = _find_data_dir()
SOURCE_DIR = DATA_DIR / "source_documents"
EXTRACTED_DIR = DATA_DIR / "extracted"

# Disclosed in the Information Document ("Current Trading and Prospects"): H1 (Jul-Dec) is
# seasonally weaker for agri clients than H2 (Jan-Jun). This ratio is our documented assumption
# for spreading a REPORTED annual figure into MODELLED months, not a reported split. Only used for
# fiscal years where we don't (yet) have a REPORTED half-year split, e.g. FY2024.
H1_SHARE_OF_YEAR = 0.40
MONTHLY_METRICS = ["revenue", "gross_profit", "operating_profit"]

# Registry of known source documents this pipeline can extract. We don't trust the model's guess
# for a file's own metadata (filename/doc_type/date/url); those are known for certain, so they're
# fixed here rather than left to the model.
DOCUMENTS: dict[str, dict[str, str | None]] = {
    "information_document": {
        "pdf": "Senus_PLC_Information_Document_2025-12.pdf",
        "doc_type": "INFORMATION_DOCUMENT",
        "published_date": "2025-12-17",  # PDF CreationDate metadata
        "url": (
            "https://live.euronext.com/sites/default/files/2025-12/"
            "SENUS%20PLC%20-%20Information%20Document.pdf"
        ),
        "json": "senus_information_document.json",
    },
    "hy2026_results": {
        "pdf": "Senus_HalfYearResults_HY2026_2026-03-19.pdf",
        "doc_type": "HALF_YEAR_RESULTS",
        "published_date": "2026-03-19",  # stated in the release
        "url": None,  # not sourced from a public URL, shared directly
        "json": "senus_hy2026_results.json",
    },
    "adf_audited_fy2025": {
        "pdf": "ADF_Farm_Solutions_Audited_Financial_Statements_2025-06-30.pdf",
        "doc_type": "AUDITED_ANNUAL_REPORT",
        "published_date": "2025-11-19",  # date the directors' report/audit opinion were signed
        "url": None,  # not sourced from a public URL, shared directly
        "json": "senus_adf_audited_fy2025.json",
    },
}


def cmd_extract(doc_key: str, dry_run: bool) -> None:
    doc = DOCUMENTS[doc_key]
    source_pdf = SOURCE_DIR / doc["pdf"]
    extracted_json = EXTRACTED_DIR / doc["json"]

    result = extract_from_pdf(source_pdf)
    result.source_document.filename = source_pdf.name
    result.source_document.doc_type = doc["doc_type"]
    result.source_document.published_date = doc["published_date"]
    result.source_document.url = doc["url"]
    payload = result.model_dump()

    print(f"Extracted {len(result.periods)} periods, {len(result.facts)} facts, "
          f"{len(result.customer_metrics)} customer metrics, {len(result.kpi_targets)} KPI targets, "
          f"{len(result.debt_instruments)} debt instruments.")

    if dry_run:
        print(json.dumps(payload, indent=2))
        return

    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
    extracted_json.write_text(json.dumps(payload, indent=2))
    print(f"Wrote {extracted_json}. Review it, then run: python scripts/ingest.py load {extracted_json}")


async def _load(result: ExtractionResult, session_factory=AsyncSessionLocal) -> None:
    # Additive load: each source document may restate figures already loaded from another one
    # (e.g. every press release repeats the "FY2025 revenue €836,991" boilerplate). We never wipe
    # existing REPORTED data on a later load; a genuine conflicting value is printed for manual
    # review rather than silently overwritten or silently dropped.
    # session_factory defaults to the real app database but is injectable so tests can point it at
    # a test database instead.
    async with session_factory() as session:
        doc = await _get_or_create_source_document(session, result)

        period_by_label: dict[str, FinancialPeriod] = {}
        for p in result.periods:
            existing = await session.scalar(
                select(FinancialPeriod).where(FinancialPeriod.label == p.label)
            )
            if existing:
                period = existing
                period.period_type = PeriodType(p.period_type)
                period.fiscal_year = p.fiscal_year
                period.start_date = date.fromisoformat(p.start_date)
                period.end_date = date.fromisoformat(p.end_date)
                period.is_actual_reported = p.is_actual_reported
            else:
                period = FinancialPeriod(
                    label=p.label,
                    period_type=PeriodType(p.period_type),
                    fiscal_year=p.fiscal_year,
                    start_date=date.fromisoformat(p.start_date),
                    end_date=date.fromisoformat(p.end_date),
                    is_actual_reported=p.is_actual_reported,
                )
                session.add(period)
                await session.flush()
            period_by_label[p.label] = period

        new_facts = 0
        for f in result.facts:
            period = period_by_label.get(f.period_label)
            if period is None:
                print(f"Skipping fact {f.metric_key}: unknown period {f.period_label}")
                continue
            existing_fact = await session.scalar(
                select(FinancialFact).where(
                    FinancialFact.period_id == period.id,
                    FinancialFact.metric_key == f.metric_key,
                )
            )
            if existing_fact is not None:
                if float(existing_fact.value) != f.value:
                    print(
                        f"CONFLICT {f.period_label}.{f.metric_key}: keeping existing "
                        f"{existing_fact.value} (source_doc_id={existing_fact.source_doc_id}), "
                        f"new extraction says {f.value} from {doc.filename} - not overwritten"
                    )
                continue
            session.add(
                FinancialFact(
                    period_id=period.id,
                    metric_key=f.metric_key,
                    value=f.value,
                    provenance=Provenance.REPORTED,
                    source_doc_id=doc.id,
                    note=f.note,
                )
            )
            new_facts += 1

        new_customer_metrics = 0
        for c in result.customer_metrics:
            period = period_by_label.get(c.period_label)
            if period is None:
                print(f"Skipping customer metric: unknown period {c.period_label}")
                continue
            existing_cm = await session.scalar(
                select(CustomerMetric).where(
                    CustomerMetric.period_id == period.id,
                    CustomerMetric.channel == CustomerChannel(c.channel),
                )
            )
            if existing_cm is not None:
                if existing_cm.customer_count != c.customer_count:
                    print(
                        f"CONFLICT {c.period_label}.{c.channel} customer_count: keeping existing "
                        f"{existing_cm.customer_count}, new extraction says {c.customer_count} - "
                        "not overwritten"
                    )
                continue
            session.add(
                CustomerMetric(
                    period_id=period.id,
                    channel=CustomerChannel(c.channel),
                    customer_count=c.customer_count,
                    avg_acv=c.avg_acv,
                    provenance=Provenance.REPORTED,
                )
            )
            new_customer_metrics += 1

        new_kpi_targets = 0
        for k in result.kpi_targets:
            existing_kpi = await session.scalar(select(KPITarget).where(KPITarget.name == k.name))
            if existing_kpi is not None:
                continue
            session.add(
                KPITarget(
                    name=k.name,
                    target_value=k.target_value,
                    target_date=date.fromisoformat(k.target_date),
                    description=k.description,
                    source_doc_id=doc.id,
                )
            )
            new_kpi_targets += 1

        new_debt_instruments = 0
        for d in result.debt_instruments:
            existing_debt = await session.scalar(
                select(DebtInstrument).where(DebtInstrument.name == d.name)
            )
            if existing_debt is not None:
                continue
            session.add(
                DebtInstrument(
                    name=d.name,
                    principal=d.principal,
                    start_date=date.fromisoformat(d.start_date),
                    provider=d.provider,
                    repaid_date=date.fromisoformat(d.repaid_date) if d.repaid_date else None,
                    note=d.note,
                    provenance=Provenance.REPORTED,
                )
            )
            new_debt_instruments += 1

        await session.commit()
        print(
            f"Loaded {new_facts} new facts, {new_customer_metrics} new customer metrics, "
            f"{new_kpi_targets} new KPI targets, {new_debt_instruments} new debt instruments "
            f"across {len(period_by_label)} periods."
        )


async def _get_or_create_source_document(session: AsyncSession, result: ExtractionResult) -> SourceDocument:
    meta = result.source_document
    existing = await session.scalar(
        select(SourceDocument).where(SourceDocument.filename == meta.filename)
    )
    if existing:
        return existing
    doc = SourceDocument(
        filename=meta.filename,
        doc_type=meta.doc_type,
        published_date=date.fromisoformat(meta.published_date) if meta.published_date else None,
        url=meta.url,
    )
    session.add(doc)
    await session.flush()
    return doc


def cmd_load(json_path: Path) -> None:
    result = ExtractionResult.model_validate_json(json_path.read_text())
    asyncio.run(_load(result))


def _split_evenly(h1_total: float, h2_total: float) -> list[float]:
    return [h1_total / 6] * 6 + [h2_total / 6] * 6  # Jul-Dec, then Jan-Jun


def _add_months(start_year: int, start_month: int, offset: int) -> tuple[int, int]:
    total = (start_month - 1) + offset
    return start_year + total // 12, total % 12 + 1


async def _find_reported_h1_share(session: AsyncSession) -> float:
    """Best available estimate of what fraction of a fiscal year's revenue falls in its first six
    months (Jul-Dec), for fiscal years where we only have the annual total and no REPORTED
    half-year actuals. Prefers a ratio measured from a real REPORTED half-year (more reliable than
    a generic assumption); only falls back to the Information Document's disclosed "H1 is
    seasonally weaker" guidance (H1_SHARE_OF_YEAR) if no REPORTED half-year data exists at all."""
    h1_periods = (
        await session.scalars(
            select(FinancialPeriod).where(
                FinancialPeriod.period_type == PeriodType.HALF_YEAR,
                FinancialPeriod.is_actual_reported.is_(True),
            )
        )
    ).all()
    for h1 in h1_periods:
        annual = await session.scalar(
            select(FinancialPeriod).where(
                FinancialPeriod.period_type == PeriodType.ANNUAL,
                FinancialPeriod.fiscal_year == h1.fiscal_year,
                FinancialPeriod.start_date == h1.start_date,
            )
        )
        if annual is None:
            continue
        h1_revenue = await session.scalar(
            select(FinancialFact.value).where(
                FinancialFact.period_id == h1.id, FinancialFact.metric_key == "revenue"
            )
        )
        annual_revenue = await session.scalar(
            select(FinancialFact.value).where(
                FinancialFact.period_id == annual.id, FinancialFact.metric_key == "revenue"
            )
        )
        if h1_revenue and annual_revenue:
            return float(h1_revenue) / float(annual_revenue)
    return H1_SHARE_OF_YEAR


async def _model_monthly(session_factory=AsyncSessionLocal) -> None:
    async with session_factory() as session:
        measured_h1_share = await _find_reported_h1_share(session)

        annual_periods = (
            await session.scalars(
                select(FinancialPeriod).where(FinancialPeriod.period_type == PeriodType.ANNUAL)
            )
        ).all()

        for annual in annual_periods:
            facts = (
                await session.scalars(
                    select(FinancialFact).where(
                        FinancialFact.period_id == annual.id,
                        FinancialFact.metric_key.in_(MONTHLY_METRICS),
                    )
                )
            ).all()
            facts_by_metric = {f.metric_key: float(f.value) for f in facts}
            if not facts_by_metric:
                continue

            # A REPORTED half-year covering this fiscal year's first six months lets us split
            # with a real H1 actual instead of an assumed percentage.
            reported_h1 = await session.scalar(
                select(FinancialPeriod).where(
                    FinancialPeriod.period_type == PeriodType.HALF_YEAR,
                    FinancialPeriod.is_actual_reported.is_(True),
                    FinancialPeriod.fiscal_year == annual.fiscal_year,
                    FinancialPeriod.start_date == annual.start_date,
                )
            )
            reported_h1_facts: dict[str, float] = {}
            if reported_h1 is not None:
                h1_fact_rows = (
                    await session.scalars(
                        select(FinancialFact).where(
                            FinancialFact.period_id == reported_h1.id,
                            FinancialFact.metric_key.in_(MONTHLY_METRICS),
                        )
                    )
                ).all()
                reported_h1_facts = {f.metric_key: float(f.value) for f in h1_fact_rows}

            existing_months = (
                await session.scalars(
                    select(FinancialPeriod).where(
                        FinancialPeriod.period_type == PeriodType.MONTHLY,
                        FinancialPeriod.fiscal_year == annual.fiscal_year,
                    )
                )
            ).all()
            for m in existing_months:
                await session.execute(delete(FinancialFact).where(FinancialFact.period_id == m.id))
                await session.delete(m)
            await session.flush()

            month_periods: list[FinancialPeriod] = []
            for i in range(12):
                year, month = _add_months(annual.start_date.year, annual.start_date.month, i)
                month_start = date(year, month, 1)
                next_year, next_month = _add_months(year, month, 1)
                month_end = date(next_year, next_month, 1)
                period = FinancialPeriod(
                    label=f"{month_start.strftime('%b %Y')}",
                    period_type=PeriodType.MONTHLY,
                    fiscal_year=annual.fiscal_year,
                    start_date=month_start,
                    end_date=month_end,
                    is_actual_reported=False,
                )
                session.add(period)
                month_periods.append(period)
            await session.flush()

            assumption_note = (
                "MODELLED: no REPORTED half-year actual exists for this fiscal year, so the "
                "annual figure is split assuming "
                f"{measured_h1_share * 100:.1f}% falls in Jul-Dec (measured from a fiscal year "
                "that does have a REPORTED half-year, or the Information Document's disclosed "
                "assumption if none exists yet). Not a reported monthly actual."
            )
            derived_note = (
                "MODELLED: monthly split assumes an even spread within each half, but the H1 "
                f"(Jul-Dec {annual.start_date.year}) total is the REPORTED {reported_h1.label if reported_h1 else ''} "
                "half-year actual, not an assumption; H2 is this REPORTED annual total minus that "
                "REPORTED H1 actual. Not itself a reported monthly actual."
            )

            for metric_key, annual_value in facts_by_metric.items():
                if metric_key in reported_h1_facts:
                    h1_total = reported_h1_facts[metric_key]
                    h2_total = annual_value - h1_total
                    note = derived_note
                else:
                    h1_total = annual_value * measured_h1_share
                    h2_total = annual_value * (1 - measured_h1_share)
                    note = assumption_note
                for period, monthly_value in zip(month_periods, _split_evenly(h1_total, h2_total)):
                    session.add(
                        FinancialFact(
                            period_id=period.id,
                            metric_key=metric_key,
                            value=round(monthly_value, 2),
                            provenance=Provenance.MODELLED,
                            note=note,
                        )
                    )

        await session.commit()
        print(f"Modelled monthly facts for {len(annual_periods)} fiscal year(s) (H1 share used for years without a REPORTED half-year: {measured_h1_share * 100:.1f}%).")


def cmd_model_monthly() -> None:
    asyncio.run(_model_monthly())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_extract = sub.add_parser("extract", help="Run Gemini extraction on a source PDF")
    p_extract.add_argument(
        "--doc",
        choices=sorted(DOCUMENTS),
        default="information_document",
        help="Which registered source document to extract (see DOCUMENTS in this file)",
    )
    p_extract.add_argument("--dry-run", action="store_true", help="Print JSON, don't write the file")

    p_load = sub.add_parser("load", help="Load reviewed extraction JSON into Postgres")
    p_load.add_argument("json_path")

    sub.add_parser("model-monthly", help="Derive MODELLED monthly splits from REPORTED annual facts")

    args = parser.parse_args()

    if args.command == "extract":
        cmd_extract(doc_key=args.doc, dry_run=args.dry_run)
    elif args.command == "load":
        cmd_load(Path(args.json_path))
    elif args.command == "model-monthly":
        cmd_model_monthly()


if __name__ == "__main__":
    main()
