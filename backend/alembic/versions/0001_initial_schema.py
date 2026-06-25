"""Create the initial library schema.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-06-19
"""

from alembic import op

from app.database import Base
import app.models  # noqa: F401 - ensure model metadata is loaded

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
