from typing import TYPE_CHECKING
import uuid

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey


from database.base import Base
from core.constants import FieldConstraints
from database.mixins import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from database.models import ShoppingListsOrm, WorkspaceMembersOrm, \
        WorkspaceChangesOrm



class WorkspacesOrm(UUIDMixin, TimestampMixin, Base):
    __tablename__ = 'workspaces'

    name: Mapped[str] = mapped_column(String(FieldConstraints.base_len))
    description: Mapped[str | None] = mapped_column(String(FieldConstraints.description_len))
    version: Mapped[int] = mapped_column(default=1)
    owner_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'))

    shopping_lists: Mapped[list['ShoppingListsOrm']] = relationship(
        back_populates='workspace',
    )

    members_roles: Mapped[list['WorkspaceMembersOrm']] = relationship(
        back_populates='workspace',
    )

    changes: Mapped['WorkspaceChangesOrm'] = relationship(
        back_populates='workspace'
    )
