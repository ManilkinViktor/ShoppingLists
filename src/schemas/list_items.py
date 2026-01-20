from typing import TYPE_CHECKING
import uuid

from pydantic import Field

from src.schemas.mixins import UUIDMixinDTO, TimeStampMixinDTO
from src.database.base import FieldConstraints

if TYPE_CHECKING:
    from src.schemas.shopping_lists import ShoppingListRelWorkspaceDTO

class ListItemDTO(UUIDMixinDTO, TimeStampMixinDTO):
    list_id: uuid.UUID
    name: str = Field(min_length=1, max_length=FieldConstraints.base_len)
    quantity: int = Field(gt=0, lt=FieldConstraints.quantity_border)
    unit: str | None = Field(max_length=FieldConstraints.base_len)
    category: str | None = Field(max_length=FieldConstraints.base_len)
    is_purchased: bool = Field(default=False)


class ListItemRelListDTO(ListItemDTO):
    list: 'ShoppingListRelWorkspaceDTO'
