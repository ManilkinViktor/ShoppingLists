from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.constants import FieldConstraints
from database.base import Base
from database.mixins import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from database.models import WorkspaceMembersOrm, RefreshSessionsOrm


class UsersOrm(UUIDMixin, TimestampMixin, Base):
    __tablename__ = 'users'

    cnt_repr_attrs = 2

    name: Mapped[str] = mapped_column(String(FieldConstraints.BASE_LEN))
    email: Mapped[str] = mapped_column(String(FieldConstraints.BASE_LEN), unique=True)
    hashed_password: Mapped[str]

    connected_workspaces: Mapped[list['WorkspaceMembersOrm']] = relationship(
        back_populates='user',
        overlaps='accessible_workspaces',
    )

    refresh_sessions: Mapped[list['RefreshSessionsOrm']] = relationship(
        back_populates='user',
        cascade='all, delete-orphan',
    )
