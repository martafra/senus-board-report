from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import CustomerChannel, PeriodType, Provenance


class FinancialPeriod(Base, TimestampMixin):
    __tablename__ = "financial_periods"

    id: Mapped[int] = mapped_column(primary_key=True)
    period_type: Mapped[PeriodType] = mapped_column(SAEnum(PeriodType, name="period_type"))
    fiscal_year: Mapped[int] = mapped_column(Integer)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    label: Mapped[str] = mapped_column(String(50))  # "FY2025", "HY2026", "Jul 2024", ...
    is_actual_reported: Mapped[bool] = mapped_column(Boolean, default=False)

    facts: Mapped[list["FinancialFact"]] = relationship(
        back_populates="period", cascade="all, delete-orphan"
    )
    customer_metrics: Mapped[list["CustomerMetric"]] = relationship(
        back_populates="period", cascade="all, delete-orphan"
    )


# key/value table: new metrics are new rows, not migrations, and each keeps its own provenance.
class FinancialFact(Base, TimestampMixin):
    __tablename__ = "financial_facts"

    id: Mapped[int] = mapped_column(primary_key=True)
    period_id: Mapped[int] = mapped_column(ForeignKey("financial_periods.id", ondelete="CASCADE"))
    metric_key: Mapped[str] = mapped_column(String(100))  # revenue, gross_profit, cash_end, ...
    value: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    provenance: Mapped[Provenance] = mapped_column(SAEnum(Provenance, name="provenance"))
    source_doc_id: Mapped[int | None] = mapped_column(
        ForeignKey("source_documents.id"), nullable=True
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    period: Mapped["FinancialPeriod"] = relationship(back_populates="facts")


class CustomerMetric(Base, TimestampMixin):
    __tablename__ = "customer_metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    period_id: Mapped[int] = mapped_column(ForeignKey("financial_periods.id", ondelete="CASCADE"))
    channel: Mapped[CustomerChannel] = mapped_column(SAEnum(CustomerChannel, name="customer_channel"))
    customer_count: Mapped[int] = mapped_column(Integer)
    avg_acv: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    provenance: Mapped[Provenance] = mapped_column(SAEnum(Provenance, name="provenance"))

    period: Mapped["FinancialPeriod"] = relationship(back_populates="customer_metrics")


class KPITarget(Base, TimestampMixin):
    __tablename__ = "kpi_targets"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    target_value: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    target_date: Mapped[date] = mapped_column(Date)
    description: Mapped[str] = mapped_column(Text)
    source_doc_id: Mapped[int | None] = mapped_column(
        ForeignKey("source_documents.id"), nullable=True
    )


class DebtInstrument(Base, TimestampMixin):
    __tablename__ = "debt_instruments"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    principal: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    start_date: Mapped[date] = mapped_column(Date)
    provider: Mapped[str] = mapped_column(String(150))
    rate_assumption: Mapped[Decimal | None] = mapped_column(Numeric(6, 4), nullable=True)
    repaid_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    provenance: Mapped[Provenance] = mapped_column(SAEnum(Provenance, name="provenance"))
