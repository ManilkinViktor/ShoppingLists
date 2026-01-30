import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base
from core.constants import FieldConstraints
from database.mixins import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from database.models import WorkspacesOrm, ListItemsOrm


class ShoppingListsOrm(UUIDMixin, TimestampMixin, Base):
    __tablename__ = 'shopping_lists'

    cnt_repr_attrs = 2

    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('workspaces.id', ondelete='CASCADE'))
    name: Mapped[str] = mapped_column(String(FieldConstraints.base_len))
    description: Mapped[str | None] = mapped_column(String(FieldConstraints.description_len))
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'))

    workspace: Mapped['WorkspacesOrm'] = relationship(
        back_populates='shopping_lists',
    )

    items: Mapped[list['ListItemsOrm']] = relationship(
        back_populates='shopping_list'
    )

