from typing import Literal

from pydantic import BaseModel, Field


class ExtractedSourceDocument(BaseModel):
    filename: str
    doc_type: str
    published_date: str | None = Field(default=None, description="ISO date, e.g. 2025-12-18")
    url: str | None = None


class ExtractedPeriod(BaseModel):
    label: str = Field(description="e.g. FY2024, FY2025, HY2026")
    period_type: Literal["ANNUAL", "HALF_YEAR", "QUARTERLY", "MONTHLY"]
    fiscal_year: int
    start_date: str = Field(description="ISO date")
    end_date: str = Field(description="ISO date")
    is_actual_reported: bool = True


class ExtractedFact(BaseModel):
    period_label: str
    metric_key: str = Field(
        description=(
            "snake_case metric name. Established conventions used across documents so the same "
            "real-world concept always gets the same key, e.g.: revenue, cost_of_sales, "
            "gross_profit, admin_expenses, other_operating_income, operating_profit, "
            "interest_expense, profit_before_tax, tax_expense, profit_after_tax, gross_margin, "
            "goodwill, development_costs, tangible_assets, debtors (balance sheet aggregate total; "
            "only use trade_debtors for a note-level 'Trade debtors' sub-line, a smaller subset of "
            "the aggregate, never for the same thing as debtors), creditors_current (aggregate; "
            "same distinction for trade_creditors), creditors_over_one_year, "
            "contingent_consideration, share_capital, share_premium, net_assets, "
            "retained_earnings, cash_start, cash_end, depreciation, cash_operating, "
            "cash_investing, cash_financing (always each section's final net total; component "
            "lines within a section get their own distinct keys, e.g. cash_financing_loans, "
            "cash_financing_share_issue), new_customers_period_{channel}, new_bookings_value_period"
        )
    )
    value: float
    note: str | None = None


class ExtractedCustomerMetric(BaseModel):
    period_label: str
    channel: Literal["ENTERPRISE", "INDEPENDENT", "RD"]
    customer_count: int
    avg_acv: float | None = None


class ExtractedKPITarget(BaseModel):
    name: str
    target_value: float
    target_date: str = Field(description="ISO date, e.g. 2030-06-30")
    description: str


class ExtractedDebtInstrument(BaseModel):
    name: str
    principal: float
    start_date: str
    provider: str
    repaid_date: str | None = Field(
        default=None,
        description=(
            "ISO date the loan was repaid, if the document discloses it as repaid. Null if it's "
            "still outstanding as at the document's reporting date."
        ),
    )
    note: str | None = Field(
        default=None,
        description="Any caveat worth keeping, e.g. when only a month/year is disclosed rather than an exact day.",
    )


class ExtractionResult(BaseModel):
    source_document: ExtractedSourceDocument
    periods: list[ExtractedPeriod]
    facts: list[ExtractedFact]
    customer_metrics: list[ExtractedCustomerMetric]
    kpi_targets: list[ExtractedKPITarget]
    debt_instruments: list[ExtractedDebtInstrument]
