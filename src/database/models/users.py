from typing import List, TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String

from database.base import Base
from core.constants import FieldConstraints
from database.mixins import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from database.models import WorkspacesOrm, WorkspaceMembersOrm



class UsersOrm(UUIDMixin, TimestampMixin, Base):
    __tablename__ = 'users'

    cnt_repr_attrs = 2

    name: Mapped[str] = mapped_column(String(FieldConstraints.base_len))
    email: Mapped[str] = mapped_column(String(FieldConstraints.base_len), unique=True)
    hashed_password: Mapped[str]


    connected_workspaces: Mapped[List['WorkspaceMembersOrm']] = relationship(
        back_populates='user',
        overlaps='accessible_workspaces',
    )



