import datetime
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, TIMESTAMP, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.enums import Role
from database.base import Base
from utils.datetime_utils import utc_now

if TYPE_CHECKING:
    from database.models import WorkspacesOrm


class WorkspaceInvitesOrm(Base):
    __tablename__ = 'workspace_invites'

    cnt_repr_attrs = 2

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('workspaces.id', ondelete='CASCADE'))
    role: Mapped[Role]
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=utc_now,
    )
    expires_at: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(timezone=True))
    max_uses: Mapped[int | None] = mapped_column(default=None)
    current_uses: Mapped[int] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column(default=True)

    __table_args__ = (
        Index('ix_workspace_invites_workspace_id', 'workspace_id'),
    )

    workspace: Mapped['WorkspacesOrm'] = relationship(back_populates='invites')
