from sqlalchemy import select

from app.models import DebtInstrument, FinancialFact, FinancialPeriod, KPITarget, SourceDocument
from scripts.ingest import _load
from app.schemas.extraction import (
    ExtractedDebtInstrument,
    ExtractedFact,
    ExtractedKPITarget,
    ExtractedPeriod,
    ExtractedSourceDocument,
    ExtractionResult,
)


def _result(
    filename: str,
    facts: list[ExtractedFact],
    kpi_targets: list[ExtractedKPITarget] | None = None,
    debt_instruments: list[ExtractedDebtInstrument] | None = None,
) -> ExtractionResult:
    return ExtractionResult(
        source_document=ExtractedSourceDocument(filename=filename, doc_type="TEST_DOC"),
        periods=[
            ExtractedPeriod(
                label="FY2025",
                period_type="ANNUAL",
                fiscal_year=2025,
                start_date="2024-07-01",
                end_date="2025-06-30",
            )
        ],
        facts=facts,
        customer_metrics=[],
        kpi_targets=kpi_targets or [],
        debt_instruments=debt_instruments or [],
    )


async def test_load_inserts_new_facts(session_factory):
    result = _result(
        "doc-a.pdf",
        [ExtractedFact(period_label="FY2025", metric_key="revenue", value=1000.0)],
    )
    await _load(result, session_factory)

    async with session_factory() as session:
        period = await session.scalar(select(FinancialPeriod).where(FinancialPeriod.label == "FY2025"))
        assert period is not None
        fact = await session.scalar(
            select(FinancialFact).where(
                FinancialFact.period_id == period.id, FinancialFact.metric_key == "revenue"
            )
        )
        assert fact is not None
        assert float(fact.value) == 1000.0


async def test_load_twice_does_not_duplicate_facts_or_documents(session_factory):
    result = _result(
        "doc-a.pdf",
        [ExtractedFact(period_label="FY2025", metric_key="revenue", value=1000.0)],
    )
    await _load(result, session_factory)
    await _load(result, session_factory)  # same document, same fact, loaded twice

    async with session_factory() as session:
        period = await session.scalar(select(FinancialPeriod).where(FinancialPeriod.label == "FY2025"))
        facts = (
            await session.scalars(
                select(FinancialFact).where(
                    FinancialFact.period_id == period.id, FinancialFact.metric_key == "revenue"
                )
            )
        ).all()
        assert len(facts) == 1

        docs = (await session.scalars(select(SourceDocument).where(SourceDocument.filename == "doc-a.pdf"))).all()
        assert len(docs) == 1


async def test_load_does_not_overwrite_conflicting_value_from_another_document(session_factory, capsys):
    first = _result(
        "doc-a.pdf",
        [ExtractedFact(period_label="FY2025", metric_key="revenue", value=1000.0)],
    )
    second = _result(
        "doc-b.pdf",
        [ExtractedFact(period_label="FY2025", metric_key="revenue", value=9999.0)],
    )
    await _load(first, session_factory)
    await _load(second, session_factory)

    async with session_factory() as session:
        period = await session.scalar(select(FinancialPeriod).where(FinancialPeriod.label == "FY2025"))
        fact = await session.scalar(
            select(FinancialFact).where(
                FinancialFact.period_id == period.id, FinancialFact.metric_key == "revenue"
            )
        )
        # the original value from doc-a is preserved, doc-b's conflicting value is not applied
        assert float(fact.value) == 1000.0

    assert "CONFLICT" in capsys.readouterr().out


async def test_load_upserts_kpi_targets_by_name(session_factory):
    target = ExtractedKPITarget(
        name="Revenue CAGR", target_value=50.0, target_date="2030-06-30", description="v1"
    )
    same_target_different_wording = ExtractedKPITarget(
        name="Revenue CAGR", target_value=50.0, target_date="2030-06-30", description="v2 restated"
    )
    await _load(_result("doc-a.pdf", [], [target]), session_factory)
    await _load(_result("doc-b.pdf", [], [same_target_different_wording]), session_factory)

    async with session_factory() as session:
        targets = (await session.scalars(select(KPITarget).where(KPITarget.name == "Revenue CAGR"))).all()
        assert len(targets) == 1
        assert targets[0].description == "v1"  # first-seen wins, not silently replaced


async def test_load_persists_debt_instrument_repaid_date_and_note(session_factory):
    repaid_loan = ExtractedDebtInstrument(
        name="Working Capital Loan - Test Director",
        principal=100000.0,
        start_date="2025-03-01",
        provider="Test Director",
        repaid_date="2025-10-31",
        note="Exact repayment day not disclosed; dated to the last day of the disclosed month.",
    )
    still_outstanding_loan = ExtractedDebtInstrument(
        name="SBCI backed term loan",
        principal=100000.0,
        start_date="2024-07-01",
        provider="SBCI",
    )
    await _load(_result("doc-a.pdf", [], debt_instruments=[repaid_loan, still_outstanding_loan]), session_factory)

    async with session_factory() as session:
        repaid = await session.scalar(
            select(DebtInstrument).where(DebtInstrument.name == "Working Capital Loan - Test Director")
        )
        assert repaid.repaid_date.isoformat() == "2025-10-31"
        assert "not disclosed" in repaid.note

        outstanding = await session.scalar(
            select(DebtInstrument).where(DebtInstrument.name == "SBCI backed term loan")
        )
        assert outstanding.repaid_date is None
        assert outstanding.note is None
