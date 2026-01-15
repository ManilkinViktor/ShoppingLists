from typing import List, TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String

from src.database.base import Base, ColumnConstraints
from src.database.mixins import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from src.database.models.workspaces import WorkspacesOrm



class UsersOrm(UUIDMixin, TimestampMixin, Base):
    __tablename__ = 'users'

    cnt_repr_attrs = 2

    name: Mapped[str] = mapped_column(String(ColumnConstraints.base_len))
    email: Mapped[str] = mapped_column(String(ColumnConstraints.base_len))
    hashed_password: Mapped[str] = mapped_column(String(ColumnConstraints.base_len))

    accessible_workspaces: Mapped[List['WorkspacesOrm']] = relationship(
        back_populates='users',
        secondary='workspace_members'
    )




