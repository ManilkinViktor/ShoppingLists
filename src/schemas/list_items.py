from typing import TYPE_CHECKING
import uuid

from pydantic import BaseModel, Field

from schemas.mixins import UUIDMixinDTO, TimeStampMixinDTO
from core.constants import FieldConstraints

if TYPE_CHECKING:
    from schemas.shopping_lists import ShoppingListRelWorkspaceDTO

class ListItemCreateDTO(UUIDMixinDTO):
    list_id: uuid.UUID
    name: str = Field(min_length=1, max_length=FieldConstraints.base_len)
    quantity: int = Field(gt=0, lt=FieldConstraints.quantity_border)
    unit: str | None = Field(max_length=FieldConstraints.base_len)
    category: str | None = Field(max_length=FieldConstraints.base_len)
    is_purchased: bool = Field(default=False)


class ListItemPatchDTO(UUIDMixinDTO):
    list_id: uuid.UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=FieldConstraints.base_len)
    delta_quantity: int | None = Field(
        default=None,
        gt=-FieldConstraints.quantity_border,
        lt=FieldConstraints.quantity_border,
        description='Additive delta to apply to current quantity',
    )
    unit: str | None = Field(default=None, max_length=FieldConstraints.base_len)
    category: str | None = Field(default=None, max_length=FieldConstraints.base_len)
    is_purchased: bool | None = None

class ListItemDTO(ListItemCreateDTO, TimeStampMixinDTO):
    pass


class ListItemsCreateDTO(BaseModel):
    list_id: uuid.UUID
    items: list[ListItemCreateDTO] = Field(default_factory=list)


class ListItemsPatchDTO(BaseModel):
    list_id: uuid.UUID
    items: list[ListItemPatchDTO] = Field(default_factory=list)


class ListItemsDeleteDTO(BaseModel):
    list_id: uuid.UUID
    ids: list[uuid.UUID] = Field(default_factory=list)


class ListItemRelListDTO(ListItemDTO):
    shopping_list: 'ShoppingListRelWorkspaceDTO'
