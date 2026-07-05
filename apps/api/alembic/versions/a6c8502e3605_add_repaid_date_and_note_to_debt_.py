"""add repaid_date and note to debt instruments

Revision ID: a6c8502e3605
Revises: 86afa5a385e7
Create Date: 2026-07-05 14:26:12.234318

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a6c8502e3605'
down_revision: Union[str, Sequence[str], None] = '86afa5a385e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("debt_instruments", sa.Column("repaid_date", sa.Date(), nullable=True))
    op.add_column("debt_instruments", sa.Column("note", sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("debt_instruments", "note")
    op.drop_column("debt_instruments", "repaid_date")
