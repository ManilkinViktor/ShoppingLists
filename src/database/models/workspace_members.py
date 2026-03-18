import datetime
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, PrimaryKeyConstraint, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.enums import Role
from database.base import Base
from utils.datetime_utils import utc_now

if TYPE_CHECKING:
    from database.models import WorkspacesOrm, UsersOrm

class WorkspaceMembersOrm(Base):
    __tablename__ = 'workspace_members'

    cnt_repr_attrs = 2

    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('workspaces.id', ondelete='CASCADE'))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    role: Mapped[Role]
    joined_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

    __table_args__ = (
        PrimaryKeyConstraint(workspace_id, user_id),
    )

    workspace: Mapped['WorkspacesOrm'] = relationship(
        back_populates='members_roles'
    )

    user: Mapped['UsersOrm'] = relationship(
        back_populates='connected_workspaces'
    )
