from typing import TYPE_CHECKING
import uuid

from pydantic import Field

from schemas.mixins import UUIDMixinDTO, TimeStampMixinDTO
from core.constants import FieldConstraints

if TYPE_CHECKING:
    from schemas.list_items import ListItemDTO
    from schemas.workspaces import WorkspaceRelUserDTO

class ShoppingListCreateDTO(UUIDMixinDTO):
    workspace_id: uuid.UUID
    name: str = Field(min_length=1, max_length=FieldConstraints.base_len)
    description: str | None = Field(max_length=FieldConstraints.base_len)
    created_by: uuid.UUID | None


class ShoppingListPatchDTO(UUIDMixinDTO):
    workspace_id: uuid.UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=FieldConstraints.base_len)
    description: str | None = Field(default=None, max_length=FieldConstraints.base_len)
    created_by: uuid.UUID | None = None

class ShoppingListDTO(ShoppingListCreateDTO, TimeStampMixinDTO):
    pass

class ShoppingListRelItemDTO(ShoppingListDTO):
    items: list['ListItemDTO'] | None

class ShoppingListRelWorkspaceDTO(ShoppingListDTO):
    workspace: 'WorkspaceRelUserDTO | None'
