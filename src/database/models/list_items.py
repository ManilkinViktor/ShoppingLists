import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.constants import FieldConstraints
from database.base import Base
from database.mixins import UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from database.models import ShoppingListsOrm


class ListItemsOrm(UUIDMixin, TimestampMixin, Base):
    __tablename__ = 'list_items'

    cnt_repr_attrs = 2

    list_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('shopping_lists.id', ondelete='CASCADE'))
    name: Mapped[str] = mapped_column(String(FieldConstraints.BASE_LEN))
    quantity: Mapped[int | None]
    unit: Mapped[str | None] = mapped_column(String(FieldConstraints.BASE_LEN))
    category: Mapped[str | None] = mapped_column(String(FieldConstraints.BASE_LEN))
    is_purchased: Mapped[bool] = mapped_column(default=False)

    shopping_list: Mapped['ShoppingListsOrm'] = relationship(
        back_populates='items',
    )

    __table_args__ = (
        CheckConstraint('quantity > 0', name='check_positive_quantity'),
    )
