import uuid
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from core.constants import FieldConstraints
from schemas.mixins import UUIDMixinDTO, TimeStampMixinDTO

if TYPE_CHECKING:
    from schemas.shopping_lists import ShoppingListRelWorkspaceDTO


class ListItemCreateDTO(UUIDMixinDTO):
    list_id: uuid.UUID
    name: str = Field(min_length=1, max_length=FieldConstraints.BASE_LEN)
    quantity: int = Field(gt=0, lt=FieldConstraints.QUANTITY_BORDER)
    unit: str | None = Field(max_length=FieldConstraints.BASE_LEN)
    category: str | None = Field(max_length=FieldConstraints.BASE_LEN)
    is_purchased: bool = Field(default=False)


class ListItemPatchDTO(UUIDMixinDTO):
    list_id: uuid.UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=FieldConstraints.BASE_LEN)
    delta_quantity: int | None = Field(
        default=None,
        gt=-FieldConstraints.QUANTITY_BORDER,
        lt=FieldConstraints.QUANTITY_BORDER,
        description='Additive delta to apply to current quantity',
    )
    unit: str | None = Field(default=None, max_length=FieldConstraints.BASE_LEN)
    category: str | None = Field(default=None, max_length=FieldConstraints.BASE_LEN)
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
