from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AIInsight(Base):
    __tablename__ = "ai_insights"

    id: Mapped[int] = mapped_column(primary_key=True)
    section_key: Mapped[str] = mapped_column(String(100))  # growth, profitability, cash, ...
    period_id: Mapped[int | None] = mapped_column(
        ForeignKey("financial_periods.id"), nullable=True
    )
    content: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(String(100))  # e.g. gemini-2.5-flash, for traceability
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    prompt_version: Mapped[str] = mapped_column(String(20))
