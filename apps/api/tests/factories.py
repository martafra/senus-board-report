"""Shared helpers for building test data directly in the (test) database, so individual tests can
set up just the periods/facts/customer metrics they need without repeating this boilerplate."""
import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models import CustomerMetric, FinancialFact, FinancialPeriod, User
from app.models.enums import CustomerChannel, PeriodType, Provenance, UserRole


async def add_period(
    session: AsyncSession,
    *,
    label: str,
    period_type: PeriodType,
    fiscal_year: int,
    start_date: datetime.date,
    end_date: datetime.date,
    is_actual_reported: bool = True,
    facts: dict[str, float] | None = None,
) -> FinancialPeriod:
    period = FinancialPeriod(
        label=label,
        period_type=period_type,
        fiscal_year=fiscal_year,
        start_date=start_date,
        end_date=end_date,
        is_actual_reported=is_actual_reported,
    )
    session.add(period)
    await session.flush()
    for metric_key, value in (facts or {}).items():
        session.add(
            FinancialFact(
                period_id=period.id, metric_key=metric_key, value=value, provenance=Provenance.REPORTED
            )
        )
    await session.commit()
    return period


async def add_annual_period(
    session: AsyncSession, *, label: str, fiscal_year: int, facts: dict[str, float] | None = None
) -> FinancialPeriod:
    return await add_period(
        session,
        label=label,
        period_type=PeriodType.ANNUAL,
        fiscal_year=fiscal_year,
        start_date=datetime.date(fiscal_year - 1, 7, 1),
        end_date=datetime.date(fiscal_year, 6, 30),
        facts=facts,
    )


async def add_customer_metric(
    session: AsyncSession, *, period: FinancialPeriod, channel: CustomerChannel, customer_count: int
) -> None:
    session.add(
        CustomerMetric(
            period_id=period.id,
            channel=channel,
            customer_count=customer_count,
            provenance=Provenance.REPORTED,
        )
    )
    await session.commit()


DEFAULT_TEST_EMAIL = "ceo@senus.com"
DEFAULT_TEST_PASSWORD = "s3cret"


async def add_user(
    session: AsyncSession, *, email: str = DEFAULT_TEST_EMAIL, password: str = DEFAULT_TEST_PASSWORD
) -> User:
    user = User(email=email, name="Test CEO", role=UserRole.CEO, hashed_password=hash_password(password))
    session.add(user)
    await session.commit()
    return user


async def login(client, *, email: str = DEFAULT_TEST_EMAIL, password: str = DEFAULT_TEST_PASSWORD) -> str:
    response = await client.post("/auth/login", data={"username": email, "password": password})
    return response.json()["access_token"]
