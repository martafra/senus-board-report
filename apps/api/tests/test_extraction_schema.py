import pytest
from pydantic import ValidationError

from app.schemas.extraction import ExtractedPeriod


def test_half_year_period_type_is_accepted():
    period = ExtractedPeriod(
        label="HY2026",
        period_type="HALF_YEAR",
        fiscal_year=2026,
        start_date="2025-07-01",
        end_date="2025-12-31",
    )
    assert period.period_type == "HALF_YEAR"


def test_unknown_period_type_is_rejected():
    with pytest.raises(ValidationError):
        ExtractedPeriod(
            label="Bogus",
            period_type="DECADE",
            fiscal_year=2026,
            start_date="2025-07-01",
            end_date="2025-12-31",
        )
