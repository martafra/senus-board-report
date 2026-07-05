"""add half_year period type

Revision ID: 86afa5a385e7
Revises: 069bf794ce4d
Create Date: 2026-07-04 17:40:36.211012

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '86afa5a385e7'
down_revision: Union[str, Sequence[str], None] = '069bf794ce4d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Postgres can't add an enum value inside a normal transaction block; Alembic's
    # autocommit_block() ends the current transaction, runs this statement on its own, then
    # resumes. IF NOT EXISTS makes this safe to re-run.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE period_type ADD VALUE IF NOT EXISTS 'HALF_YEAR'")


def downgrade() -> None:
    """Downgrade schema."""
    # Postgres has no ALTER TYPE ... DROP VALUE. Recreate the enum without HALF_YEAR, refusing
    # if any row would lose its value.
    op.execute(
        "DO $$ BEGIN "
        "IF EXISTS (SELECT 1 FROM financial_periods WHERE period_type = 'HALF_YEAR') THEN "
        "RAISE EXCEPTION "
        "'Cannot downgrade: HALF_YEAR financial_periods rows exist, delete them first'; "
        "END IF; "
        "END $$;"
    )
    op.execute("ALTER TYPE period_type RENAME TO period_type_old")
    op.execute("CREATE TYPE period_type AS ENUM ('ANNUAL', 'QUARTERLY', 'MONTHLY')")
    op.execute(
        "ALTER TABLE financial_periods ALTER COLUMN period_type "
        "TYPE period_type USING period_type::text::period_type"
    )
    op.execute("DROP TYPE period_type_old")
