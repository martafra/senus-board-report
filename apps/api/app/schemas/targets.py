from pydantic import BaseModel


class KPITargetOut(BaseModel):
    name: str
    target_value: float
    target_date: str
    description: str


class DebtInstrumentOut(BaseModel):
    name: str
    principal: float
    start_date: str
    provider: str
    repaid_date: str | None
    note: str | None
