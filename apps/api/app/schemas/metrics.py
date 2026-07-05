from typing import Literal

from pydantic import BaseModel


class MetricValue(BaseModel):
    value: float
    unit: Literal["EUR", "%", "x", "count"]
    description: str  # plain-language explanation, meant for a UI tooltip


class PeriodMetrics(BaseModel):
    period_label: str
    period_type: str
    start_date: str
    end_date: str
    is_actual_reported: bool
    metrics: dict[str, MetricValue]
