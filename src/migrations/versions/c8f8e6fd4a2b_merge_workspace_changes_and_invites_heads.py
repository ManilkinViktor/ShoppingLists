"""merge workspace changes and invites heads

Revision ID: c8f8e6fd4a2b
Revises: 9b759d1aa478, d4c2e1f8a9b3
Create Date: 2026-03-25 20:00:00.000000

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "c8f8e6fd4a2b"
down_revision: Union[str, Sequence[str], None] = ("9b759d1aa478", "d4c2e1f8a9b3")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""


def downgrade() -> None:
    """Downgrade schema."""
