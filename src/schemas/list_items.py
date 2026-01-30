from typing import TYPE_CHECKING
import uuid

from pydantic import Field

from schemas.mixins import UUIDMixinDTO, TimeStampMixinDTO
from core.constants import FieldConstraints

if TYPE_CHECKING:
    from schemas.shopping_lists import ShoppingListRelWorkspaceDTO

class ListItemAddDTO(UUIDMixinDTO):
    list_id: uuid.UUID
    name: str = Field(min_length=1, max_length=FieldConstraints.base_len)
    quantity: int = Field(gt=0, lt=FieldConstraints.quantity_border)
    unit: str | None = Field(max_length=FieldConstraints.base_len)
    category: str | None = Field(max_length=FieldConstraints.base_len)
    is_purchased: bool = Field(default=False)

class ListItemDTO(ListItemAddDTO, TimeStampMixinDTO):
    pass


class ListItemRelListDTO(ListItemDTO):
    shopping_list: 'ShoppingListRelWorkspaceDTO'
