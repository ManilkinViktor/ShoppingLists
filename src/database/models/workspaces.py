from typing import TYPE_CHECKING, List
import uuid

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey

from src.database.base import Base, ColumnConstraints
from src.database.mixins import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from src.database.models.shopping_lists import ShoppingListsOrm
    from src.database.models.users import UsersOrm


class WorkspacesOrm(UUIDMixin, TimestampMixin, Base):
    __tablename__ = 'workspaces'

    name: Mapped[str] = mapped_column(String(ColumnConstraints.base_len))
    description: Mapped[str | None] = mapped_column(String(ColumnConstraints.description_len))
    owner_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'))

    shopping_lists: Mapped[List['ShoppingListsOrm']] = relationship(
        back_populates='workspace',
    )

    users: Mapped['UsersOrm'] = relationship(
        back_populates='accessible_workspaces',
        secondary='workspace_members'
    )
