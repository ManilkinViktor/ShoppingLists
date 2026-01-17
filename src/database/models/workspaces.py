
from typing import TYPE_CHECKING, List
import uuid

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey


from src.database.base import Base, FieldConstraints
from src.database.mixins import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from src.database.models import ShoppingListsOrm, WorkspaceMembersOrm



class WorkspacesOrm(UUIDMixin, TimestampMixin, Base):
    __tablename__ = 'workspaces'

    name: Mapped[str] = mapped_column(String(FieldConstraints.base_len))
    description: Mapped[str | None] = mapped_column(String(FieldConstraints.description_len))
    owner_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'))

    shopping_lists: Mapped[List['ShoppingListsOrm']] = relationship(
        back_populates='workspace',
    )

    members_roles: Mapped[List['WorkspaceMembersOrm']] = relationship(
        back_populates='workspace',
    )
