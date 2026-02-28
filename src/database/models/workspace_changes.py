from typing import TYPE_CHECKING, Any
import datetime
import uuid


from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import TIMESTAMP, ForeignKey, PrimaryKeyConstraint, JSON

from database.base import Base
from utils.datetime_utils import utc_now

if TYPE_CHECKING:
    from database.models import WorkspacesOrm

class WorkspaceChangesOrm(Base):
    __tablename__ = 'workspace_changes'

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey('workspaces.id', ondelete='CASCADE')
    )
    workspace_version: Mapped[int]
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=utc_now
    )
    change: Mapped[dict[str, Any]] = mapped_column(JSON)

    workspace: Mapped['WorkspacesOrm'] = relationship(
        back_populates='changes'
    )

    __table_args__ = (
        PrimaryKeyConstraint('workspace_id', 'workspace_version'),
    )

