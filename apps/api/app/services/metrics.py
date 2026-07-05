from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CustomerMetric, FinancialFact, FinancialPeriod
from app.models.enums import PeriodType
from app.schemas.metrics import MetricValue, PeriodMetrics

DESCRIPTIONS = {
    "revenue": "Total sales recorded in the period.",
    "gross_margin": (
        "Of every euro of sales, how much is left after the direct cost of delivering it."
    ),
    "operating_margin": (
        "Of every euro of sales, how much is left after all running costs, before interest and tax."
    ),
    "ebitda": (
        "How much the core business earns before interest, tax and depreciation - a way to judge "
        "day-to-day operating performance on its own, regardless of how the company is financed."
    ),
    "ebitda_margin": "EBITDA as a percentage of revenue.",
    "cost_of_sales": "The direct cost of delivering what was sold, e.g. hosting and delivery costs.",
    "admin_expenses": "Running costs of the business not directly tied to a sale, e.g. salaries, rent, professional fees.",
    "distribution_costs": "Costs of marketing and selling the product to customers.",
    "yoy_growth": "How much this figure changed compared to the same period one year earlier.",
    "mom_growth": "How much this figure changed compared to the previous month.",
    "customers_enterprise": "Number of Enterprise customer accounts.",
    "customers_independent": "Number of Independent customer accounts.",
    "customers_rd": "Number of R&D customer accounts.",
    "new_customers_period_enterprise": "New Enterprise customers signed during the period.",
    "new_bookings_value_period": "Value of deals closed with new customers during the period.",
    "open_pipeline_value": "Value of deals still being negotiated, not yet closed, as at the period end.",
    "free_cash_flow": (
        "Cash generated (or used) by the business after paying for its day-to-day operations and "
        "its investment in equipment: what's actually left over in the bank."
    ),
    "operating_cash_adjustments": (
        "The gap between EBITDA and the cash the business actually generated from operations: "
        "movements in money owed to/by the company, plus interest and tax paid in the period."
    ),
    "cash_investing": "Cash spent on (or received from) equipment and other long-term investments in the period.",
    "cash_runway_months": (
        "At the current rate of spending more cash than it brings in, how many months of cash the "
        "company has left before running out."
    ),
    "working_capital": (
        "Cash plus money owed to the company, minus money the company owes suppliers/others in the "
        "short term. A rough measure of how much cash is tied up in day-to-day running of the business."
    ),
    "dscr": (
        "Debt Service Coverage Ratio: how many times over the company's earnings could cover the "
        "loan repayments and interest due this year. Below 1 means it can't cover them from earnings "
        "alone."
    ),
    "roce": (
        "Return on Capital Employed: for every euro invested in the company (by shareholders and "
        "lenders combined), how much operating profit it produced."
    ),
}

# How many calendar months a period spans, used to annualise/de-annualise cash-flow figures.
_MONTHS_IN_PERIOD = {
    PeriodType.ANNUAL: 12,
    PeriodType.HALF_YEAR: 6,
    PeriodType.MONTHLY: 1,
}


async def _facts_by_period(
    session: AsyncSession, period_types: list[PeriodType]
) -> list[tuple[FinancialPeriod, dict[str, Decimal]]]:
    periods = (
        await session.scalars(
            select(FinancialPeriod)
            .where(FinancialPeriod.period_type.in_(period_types))
            .order_by(FinancialPeriod.start_date)
        )
    ).all()
    result = []
    for period in periods:
        facts = (
            await session.scalars(select(FinancialFact).where(FinancialFact.period_id == period.id))
        ).all()
        result.append((period, {f.metric_key: f.value for f in facts}))
    return result


def _percent(numerator: Decimal, denominator: Decimal, description: str) -> MetricValue:
    return MetricValue(
        value=round(float(numerator) / float(denominator) * 100, 2),
        unit="%",
        description=description,
    )


def _amount(value: Decimal, description: str) -> MetricValue:
    return MetricValue(value=round(float(value), 2), unit="EUR", description=description)


def _count(value: int, description: str) -> MetricValue:
    return MetricValue(value=float(value), unit="count", description=description)


def _ratio(value: Decimal, description: str) -> MetricValue:
    return MetricValue(value=round(float(value), 2), unit="x", description=description)


def _ebitda(facts: dict[str, Decimal]) -> Decimal | None:
    """EBITDA = operating_profit + depreciation. Both are REPORTED facts (depreciation comes from
    the cash flow reconciliation), so this needs no assumed amortisation figure for the periods
    currently loaded (none have disclosed an intangible amortisation charge yet)."""
    operating_profit = facts.get("operating_profit")
    depreciation = facts.get("depreciation")
    if operating_profit is None or depreciation is None:
        return None
    return operating_profit + depreciation


def _year_before(d: date) -> date:
    return d.replace(year=d.year - 1)


def _month_before(d: date) -> date:
    if d.month == 1:
        return d.replace(year=d.year - 1, month=12)
    return d.replace(month=d.month - 1)


def _find_facts(
    periods_and_facts: list[tuple[FinancialPeriod, dict[str, Decimal]]],
    period_type: PeriodType,
    start_date: date,
) -> dict[str, Decimal] | None:
    for period, facts in periods_and_facts:
        if period.period_type == period_type and period.start_date == start_date:
            return facts
    return None


async def compute_profitability(session: AsyncSession) -> list[PeriodMetrics]:
    """Gross/operating/EBITDA margin, plus a cost breakdown, per ANNUAL and HALF_YEAR period."""
    facts_by_period = await _facts_by_period(session, [PeriodType.ANNUAL, PeriodType.HALF_YEAR])

    output = []
    for period, facts in facts_by_period:
        revenue = facts.get("revenue")
        gross_profit = facts.get("gross_profit")
        operating_profit = facts.get("operating_profit")
        ebitda = _ebitda(facts)

        metrics: dict[str, MetricValue] = {}
        if revenue and gross_profit is not None:
            metrics["gross_margin"] = _percent(gross_profit, revenue, DESCRIPTIONS["gross_margin"])
        if revenue and operating_profit is not None:
            metrics["operating_margin"] = _percent(
                operating_profit, revenue, DESCRIPTIONS["operating_margin"]
            )
        if ebitda is not None:
            metrics["ebitda"] = _amount(ebitda, DESCRIPTIONS["ebitda"])
            if revenue:
                metrics["ebitda_margin"] = _percent(ebitda, revenue, DESCRIPTIONS["ebitda_margin"])

        for cost_key in ("cost_of_sales", "admin_expenses", "distribution_costs"):
            value = facts.get(cost_key)
            if value is not None:
                metrics[cost_key] = _amount(value, DESCRIPTIONS[cost_key])

        output.append(_period_metrics(period, metrics))
    return output


async def compute_growth(session: AsyncSession) -> list[PeriodMetrics]:
    """Revenue, YoY growth (any period type, vs. the same period one year earlier), MoM growth
    (MONTHLY only, vs. the previous month), customer counts by channel, and bookings figures for
    whichever periods report them."""
    facts_by_period = await _facts_by_period(
        session, [PeriodType.ANNUAL, PeriodType.HALF_YEAR, PeriodType.MONTHLY]
    )
    customer_counts = await _customer_counts_by_period(session)

    output = []
    for period, facts in facts_by_period:
        metrics: dict[str, MetricValue] = {}
        revenue = facts.get("revenue")
        if revenue is not None:
            metrics["revenue"] = _amount(revenue, DESCRIPTIONS["revenue"])

            prior_year_facts = _find_facts(
                facts_by_period, period.period_type, _year_before(period.start_date)
            )
            prior_year_revenue = prior_year_facts.get("revenue") if prior_year_facts else None
            if prior_year_revenue:
                metrics["yoy_growth"] = _percent(
                    revenue - prior_year_revenue, prior_year_revenue, DESCRIPTIONS["yoy_growth"]
                )

            if period.period_type == PeriodType.MONTHLY:
                prior_month_facts = _find_facts(
                    facts_by_period, PeriodType.MONTHLY, _month_before(period.start_date)
                )
                prior_month_revenue = (
                    prior_month_facts.get("revenue") if prior_month_facts else None
                )
                if prior_month_revenue:
                    metrics["mom_growth"] = _percent(
                        revenue - prior_month_revenue, prior_month_revenue, DESCRIPTIONS["mom_growth"]
                    )

        for channel_key, count in customer_counts.get(period.id, {}).items():
            metrics[f"customers_{channel_key}"] = _count(count, DESCRIPTIONS[f"customers_{channel_key}"])

        for bookings_key in (
            "new_customers_period_enterprise",
            "new_bookings_value_period",
            "open_pipeline_value",
        ):
            value = facts.get(bookings_key)
            if value is None:
                continue
            unit_fn = _count if bookings_key == "new_customers_period_enterprise" else _amount
            metrics[bookings_key] = unit_fn(value, DESCRIPTIONS[bookings_key])

        output.append(_period_metrics(period, metrics))
    return output


async def _customer_counts_by_period(session: AsyncSession) -> dict[int, dict[str, int]]:
    rows = (await session.scalars(select(CustomerMetric))).all()
    result: dict[int, dict[str, int]] = {}
    for row in rows:
        result.setdefault(row.period_id, {})[row.channel.value.lower()] = row.customer_count
    return result


async def compute_cash_liquidity(session: AsyncSession) -> list[PeriodMetrics]:
    """EBITDA-to-Free-Cash-Flow bridge: ebitda, operating_cash_adjustments (the working
    capital/interest/tax gap between EBITDA and cash_operating), cash_investing, and
    free_cash_flow (= cash_operating + cash_investing) sum together consistently so the frontend
    can chart the walk from one to the other. Also cash runway in months (only when the business
    is actually burning cash), and working capital (only for ANNUAL/HALF_YEAR periods, where
    debtors/creditors_current are disclosed)."""
    facts_by_period = await _facts_by_period(session, [PeriodType.ANNUAL, PeriodType.HALF_YEAR])

    output = []
    for period, facts in facts_by_period:
        metrics: dict[str, MetricValue] = {}
        ebitda = _ebitda(facts)
        if ebitda is not None:
            metrics["ebitda"] = _amount(ebitda, DESCRIPTIONS["ebitda"])

        cash_operating = facts.get("cash_operating")
        cash_investing = facts.get("cash_investing")
        if cash_operating is not None and cash_investing is not None:
            metrics["free_cash_flow"] = _amount(
                cash_operating + cash_investing, DESCRIPTIONS["free_cash_flow"]
            )
            metrics["cash_investing"] = _amount(cash_investing, DESCRIPTIONS["cash_investing"])
            if ebitda is not None:
                metrics["operating_cash_adjustments"] = _amount(
                    cash_operating - ebitda, DESCRIPTIONS["operating_cash_adjustments"]
                )

        cash_end = facts.get("cash_end")
        if cash_operating is not None and cash_operating < 0 and cash_end is not None:
            months = _MONTHS_IN_PERIOD[period.period_type]
            monthly_burn = -cash_operating / months
            if monthly_burn > 0:
                metrics["cash_runway_months"] = _ratio(
                    cash_end / monthly_burn, DESCRIPTIONS["cash_runway_months"]
                )

        debtors = facts.get("debtors")
        creditors_current = facts.get("creditors_current")
        if debtors is not None and creditors_current is not None and cash_end is not None:
            working_capital = debtors + cash_end + creditors_current  # creditors_current is negative
            metrics["working_capital"] = _amount(working_capital, DESCRIPTIONS["working_capital"])

        output.append(_period_metrics(period, metrics))
    return output


async def compute_solvency(session: AsyncSession) -> list[PeriodMetrics]:
    """Debt Service Coverage Ratio, ANNUAL periods only: half-year releases haven't disclosed the
    loan repayment schedule (loans_repayable_one_year_or_less) that DSCR needs, so it isn't
    approximated at that granularity, it's simply not shown."""
    facts_by_period = await _facts_by_period(session, [PeriodType.ANNUAL])

    output = []
    for period, facts in facts_by_period:
        metrics: dict[str, MetricValue] = {}
        ebitda = _ebitda(facts)
        interest_expense = facts.get("interest_expense")
        principal_due = facts.get("loans_repayable_one_year_or_less")
        if ebitda is not None and interest_expense is not None and principal_due is not None:
            debt_service = interest_expense + principal_due
            if debt_service != 0:
                metrics["dscr"] = _ratio(ebitda / debt_service, DESCRIPTIONS["dscr"])

        output.append(_period_metrics(period, metrics))
    return output


async def compute_returns(session: AsyncSession) -> list[PeriodMetrics]:
    """ROCE = operating_profit / (Total Assets - Current Liabilities), using period-end balances
    (not an opening/closing average: we don't have every period's opening balance sheet). Total
    Assets is the sum of whichever disclosed asset facts exist for that period; goodwill and
    development_costs only exist from HY2026 (the Loamin acquisition) onward."""
    facts_by_period = await _facts_by_period(session, [PeriodType.ANNUAL, PeriodType.HALF_YEAR])

    output = []
    for period, facts in facts_by_period:
        metrics: dict[str, MetricValue] = {}
        operating_profit = facts.get("operating_profit")
        tangible_assets = facts.get("tangible_assets")
        debtors = facts.get("debtors")
        cash_end = facts.get("cash_end")
        creditors_current = facts.get("creditors_current")

        if None not in (operating_profit, tangible_assets, debtors, cash_end, creditors_current):
            total_assets = (
                tangible_assets
                + debtors
                + cash_end
                + facts.get("goodwill", 0)
                + facts.get("development_costs", 0)
            )
            capital_employed = total_assets + creditors_current  # creditors_current is negative
            if capital_employed != 0:
                metrics["roce"] = _percent(operating_profit, capital_employed, DESCRIPTIONS["roce"])

        output.append(_period_metrics(period, metrics))
    return output


def _period_metrics(period: FinancialPeriod, metrics: dict[str, MetricValue]) -> PeriodMetrics:
    return PeriodMetrics(
        period_label=period.label,
        period_type=period.period_type.value,
        start_date=period.start_date.isoformat(),
        end_date=period.end_date.isoformat(),
        is_actual_reported=period.is_actual_reported,
        metrics=metrics,
    )
