"""Create (or update the password of) the demo login user, from DEMO_USER_EMAIL/DEMO_USER_PASSWORD
in .env.

Usage (from apps/api, with the venv active, or `docker compose exec api ...`):
    python scripts/seed_user.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.db import AsyncSessionLocal  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models import User  # noqa: E402
from app.models.enums import UserRole  # noqa: E402


async def _seed() -> None:
    settings = get_settings()
    if not settings.demo_user_email or not settings.demo_user_password:
        raise SystemExit("Set DEMO_USER_EMAIL and DEMO_USER_PASSWORD in .env first.")

    async with AsyncSessionLocal() as session:
        user = await session.scalar(select(User).where(User.email == settings.demo_user_email))
        if user is None:
            session.add(
                User(
                    email=settings.demo_user_email,
                    name="Senus CEO (demo)",
                    role=UserRole.CEO,
                    hashed_password=hash_password(settings.demo_user_password),
                )
            )
            print(f"Created demo user {settings.demo_user_email}")
        else:
            user.hashed_password = hash_password(settings.demo_user_password)
            print(f"Updated password for existing user {settings.demo_user_email}")
        await session.commit()


if __name__ == "__main__":
    asyncio.run(_seed())
