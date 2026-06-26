"""reader cccd

Revision ID: 0004_reader_cccd
Revises: 0003_ticket_reservations
Create Date: 2026-06-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_reader_cccd"
down_revision: str | None = "0003_ticket_reservations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("readers", sa.Column("cccd", sa.String(length=20), nullable=True))
    op.create_index("ix_readers_cccd", "readers", ["cccd"], unique=True)
    op.add_column("card_requests", sa.Column("cccd", sa.String(length=20), nullable=True))
    op.create_index("ix_card_requests_cccd", "card_requests", ["cccd"])


def downgrade() -> None:
    op.drop_index("ix_card_requests_cccd", table_name="card_requests")
    op.drop_column("card_requests", "cccd")
    op.drop_index("ix_readers_cccd", table_name="readers")
    op.drop_column("readers", "cccd")
