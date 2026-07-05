from datetime import datetime

from pydantic import BaseModel, ConfigDict


class InsightOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    section_key: str
    content: str
    model: str
    generated_at: datetime
    prompt_version: str
