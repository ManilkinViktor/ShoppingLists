from typing import TYPE_CHECKING
import uuid

from pydantic import Field, BaseModel

from schemas.mixins import UUIDMixinDTO, TimeStampMixinDTO
from core.constants import FieldConstraints
from database.models.workspace_members import Role

if TYPE_CHECKING:
    from schemas.shopping_lists import ShoppingListRelItemDTO
    from schemas.workspace_members import WorkspaceMembersRelUserDTO

class WorkspaceAddDTO(UUIDMixinDTO):
    name: str = Field(min_length=1, max_length=FieldConstraints.base_len)
    description: str | None = Field(max_length=FieldConstraints.base_len)
    owner_id: uuid.UUID | None

class WorkspaceDTO(WorkspaceAddDTO, TimeStampMixinDTO):
    pass

class WorkspaceRelListDTO(WorkspaceDTO):
    shopping_lists: list['ShoppingListRelItemDTO'] | None


class WorkspaceRelUserDTO(WorkspaceDTO):
    members_roles: list['WorkspaceMembersRelUserDTO'] | None
