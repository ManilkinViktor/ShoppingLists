from typing import List, TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String

from src.database.base import Base, FieldConstraints
from src.database.mixins import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from src.database.models import WorkspacesOrm, WorkspaceMembersOrm



class UsersOrm(UUIDMixin, TimestampMixin, Base):
    __tablename__ = 'users'

    cnt_repr_attrs = 2

    name: Mapped[str] = mapped_column(String(FieldConstraints.base_len))
    email: Mapped[str] = mapped_column(String(FieldConstraints.base_len))
    hashed_password: Mapped[str]


    connected_workspaces: Mapped[List['WorkspaceMembersOrm']] = relationship(
        back_populates='user',
        overlaps='accessible_workspaces',
    )



