"""add refresh sessions

Revision ID: 96c9a63e5f7b
Revises: 3f7a1f4d9c2b
Create Date: 2026-02-26 10:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "96c9a63e5f7b"
down_revision: Union[str, Sequence[str], None] = "3f7a1f4d9c2b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "refresh_sessions",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("jti", sa.UUID(), nullable=False),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("jti"),
    )
    op.create_index(
        "ix_refresh_sessions_user_active",
        "refresh_sessions",
        ["user_id", "revoked_at", "expires_at"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_refresh_sessions_user_active", table_name="refresh_sessions")
    op.drop_table("refresh_sessions")
