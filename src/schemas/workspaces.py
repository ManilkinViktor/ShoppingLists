from typing import List, TYPE_CHECKING
import uuid

from pydantic import Field

from schemas.mixins import UUIDMixinDTO, TimeStampMixinDTO
from core.constants import FieldConstraints

if TYPE_CHECKING:
    from schemas.shopping_lists import ShoppingListRelItemDTO
    from schemas.workspace_members import WorkspaceMembersRelUserDTO


class WorkspaceDTO(UUIDMixinDTO, TimeStampMixinDTO):
    name: str = Field(min_length=1, max_length=FieldConstraints.base_len)
    description: str | None = Field(max_length=FieldConstraints.base_len)
    owner_id: uuid.UUID | None

class WorkspaceRelListDTO(WorkspaceDTO):
    shopping_lists: List['ShoppingListRelItemDTO'] | None


class WorkspaceRelUserDTO(WorkspaceDTO):
    joined_users: List['WorkspaceMembersRelUserDTO'] | None

