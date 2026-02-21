"""add workspace version

Revision ID: 0b2d91b13d5e
Revises: 53f80eca6382
Create Date: 2026-02-21 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0b2d91b13d5e"
down_revision: Union[str, Sequence[str], None] = "53f80eca6382"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "workspaces",
        sa.Column("version", sa.Integer(), nullable=True),
    )
    op.execute("UPDATE workspaces SET version = 1 WHERE version IS NULL")
    op.alter_column("workspaces", "version", nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("workspaces", "version")
