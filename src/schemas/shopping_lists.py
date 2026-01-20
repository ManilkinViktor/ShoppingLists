from typing import TYPE_CHECKING, List
import uuid

from pydantic import Field

from src.schemas.mixins import UUIDMixinDTO, TimeStampMixinDTO
from src.database.base import FieldConstraints

if TYPE_CHECKING:
    from src.schemas.list_items import ListItemDTO
    from src.schemas.workspaces import WorkspaceRelUserDTO

class ShoppingListDTO(UUIDMixinDTO, TimeStampMixinDTO):
    workspace_id: uuid.UUID
    name: str = Field(min_length=1, max_length=FieldConstraints.base_len)
    description: str | None = Field(max_length=FieldConstraints.base_len)
    created_by: uuid.UUID | None

class ShoppingListRelItemDTO(ShoppingListDTO):
    items: List['ListItemDTO'] | None

class ShoppingListRelWorkspaceDTO(ShoppingListDTO):
    workspace: 'WorkspaceRelUserDTO | None'