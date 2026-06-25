"""Add operational fields, acquisition details, and editable settings.

Revision ID: 0002_operations_and_settings
Revises: 0001_initial_schema
Create Date: 2026-06-20
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_operations_and_settings"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def _has_column(inspector, table: str, column: str) -> bool:
    return column in {item["name"] for item in inspector.get_columns(table)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    additions = {
        "book_titles": [
            sa.Column("edition", sa.String(length=80), nullable=True),
            sa.Column("language", sa.String(length=60), nullable=True),
            sa.Column("image_url", sa.String(length=500), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        ],
        "book_copies": [sa.Column("condition_note", sa.String(length=300), nullable=True)],
        "readers": [
            sa.Column("date_of_birth", sa.Date(), nullable=True),
            sa.Column("registered_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        ],
        "loans": [sa.Column("renewal_count", sa.Integer(), nullable=False, server_default="0")],
        "suppliers": [sa.Column("address", sa.String(length=300), nullable=True)],
        "acquisitions": [
            sa.Column("note", sa.String(length=300), nullable=True),
            sa.Column("created_by_id", sa.Integer(), nullable=True),
        ],
        "payments": [sa.Column("received_by_id", sa.Integer(), nullable=True)],
    }
    for table, columns in additions.items():
        for column in columns:
            if not _has_column(inspector, table, column.name):
                op.add_column(table, column)

    tables = set(inspector.get_table_names())
    if "acquisition_items" not in tables:
        op.create_table(
            "acquisition_items",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("acquisition_id", sa.Integer(), sa.ForeignKey("acquisitions.id", ondelete="CASCADE"), nullable=False),
            sa.Column("book_title_id", sa.Integer(), sa.ForeignKey("book_titles.id"), nullable=False),
            sa.Column("quantity", sa.Integer(), nullable=False),
            sa.Column("unit_price", sa.Integer(), nullable=False),
        )
        op.create_index("ix_acquisition_items_acquisition_id", "acquisition_items", ["acquisition_id"])
        op.create_index("ix_acquisition_items_book_title_id", "acquisition_items", ["book_title_id"])
    if "system_settings" not in tables:
        op.create_table(
            "system_settings",
            sa.Column("key", sa.String(length=80), primary_key=True),
            sa.Column("value", sa.String(length=255), nullable=False),
            sa.Column("description", sa.String(length=300), nullable=True),
        )


def downgrade() -> None:
    # Initial deployments are intentionally forward-only: operational history
    # (loans, purchases and settings) must not be discarded by accident.
    pass
