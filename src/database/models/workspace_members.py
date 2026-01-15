import datetime
import enum, uuid

from sqlalchemy import ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.base import Base
from src.utils.datetime_utils import utc_now

class Role(enum.StrEnum):
    viewer = 'viewer'
    editor = 'editor'


class WorkspaceMembersOrm(Base):
    __tablename__ = 'workspace_members'

    cnt_repr_attrs = 2

    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('workspaces.id', ondelete='CASCADE'))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    role: Mapped[Role]
    joined_at: Mapped[datetime.datetime] = mapped_column(default=utc_now)

    __table_args__ = (
        PrimaryKeyConstraint(workspace_id, user_id),
    )

