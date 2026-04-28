import uuid
from typing import TYPE_CHECKING

from pydantic import Field

from core.constants import FieldConstraints
from schemas.list_items import ListItemCreateDTO, ListItemPatchDTO
from schemas.mixins import UUIDMixinDTO, TimeStampMixinDTO

if TYPE_CHECKING:
    from schemas.list_items import ListItemDTO
    from schemas.workspaces import WorkspaceRelUserDTO


class ShoppingListCreateDTO(UUIDMixinDTO):
    workspace_id: uuid.UUID
    name: str = Field(min_length=1, max_length=FieldConstraints.BASE_LEN)
    description: str | None = Field(max_length=FieldConstraints.DESCRIPTION_LEN)
    created_by: uuid.UUID | None = None


class ShoppingListPatchDTO(UUIDMixinDTO):
    name: str | None = Field(default=None, min_length=1, max_length=FieldConstraints.BASE_LEN)
    description: str | None = Field(default=None, max_length=FieldConstraints.DESCRIPTION_LEN)


class ShoppingListPatchFullDTO(ShoppingListPatchDTO):
    create_items: list[ListItemCreateDTO] = Field(default_factory=list)
    patch_items: list[ListItemPatchDTO] = Field(default_factory=list)
    delete_item_ids: list[uuid.UUID] = Field(default_factory=list)


class ShoppingListDTO(ShoppingListCreateDTO, TimeStampMixinDTO):
    pass


class ShoppingListRelItemDTO(ShoppingListDTO):
    items: list['ListItemDTO'] | None


class ShoppingListRelWorkspaceDTO(ShoppingListDTO):
    workspace: 'WorkspaceRelUserDTO | None'
