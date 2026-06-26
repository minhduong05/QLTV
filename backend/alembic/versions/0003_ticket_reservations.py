"""borrow ticket reservations

Revision ID: 0003_ticket_reservations
Revises: 0002_operations_and_settings
Create Date: 2026-06-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_ticket_reservations"
down_revision: str | None = "0002_operations_and_settings"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "borrow_ticket_reservations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ticket_item_id", sa.Integer(), sa.ForeignKey("borrow_ticket_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("book_copy_id", sa.Integer(), sa.ForeignKey("book_copies.id"), nullable=False),
    )
    op.create_index("ix_borrow_ticket_reservations_ticket_item_id", "borrow_ticket_reservations", ["ticket_item_id"])
    op.create_index("ix_borrow_ticket_reservations_book_copy_id", "borrow_ticket_reservations", ["book_copy_id"])


def downgrade() -> None:
    op.drop_index("ix_borrow_ticket_reservations_book_copy_id", table_name="borrow_ticket_reservations")
    op.drop_index("ix_borrow_ticket_reservations_ticket_item_id", table_name="borrow_ticket_reservations")
    op.drop_table("borrow_ticket_reservations")
