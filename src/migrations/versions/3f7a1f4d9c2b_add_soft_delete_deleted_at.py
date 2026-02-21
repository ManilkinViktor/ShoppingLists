"""add soft delete deleted_at

Revision ID: 3f7a1f4d9c2b
Revises: 0b2d91b13d5e
Create Date: 2026-02-21 12:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3f7a1f4d9c2b"
down_revision: Union[str, Sequence[str], None] = "0b2d91b13d5e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("users", sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column("workspaces", sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column("shopping_lists", sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column("list_items", sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("list_items", "deleted_at")
    op.drop_column("shopping_lists", "deleted_at")
    op.drop_column("workspaces", "deleted_at")
    op.drop_column("users", "deleted_at")
