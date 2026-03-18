from typing import TYPE_CHECKING
import uuid

from pydantic import Field

from core.enums import Role

from schemas.mixins import UUIDMixinDTO, TimeStampMixinDTO
from core.constants import FieldConstraints

if TYPE_CHECKING:
    from schemas.shopping_lists import ShoppingListRelItemDTO
    from schemas.workspace_members import WorkspaceMembersRelUserDTO

class WorkspaceCreateDTO(UUIDMixinDTO):
    name: str = Field(min_length=1, max_length=FieldConstraints.base_len)
    description: str | None = Field(max_length=FieldConstraints.base_len)
    owner_id: uuid.UUID | None = None


class WorkspacePatchDTO(UUIDMixinDTO):
    name: str | None = Field(default=None, min_length=1, max_length=FieldConstraints.base_len)
    description: str | None = Field(default=None, max_length=FieldConstraints.base_len)

class WorkspaceDTO(WorkspaceCreateDTO, TimeStampMixinDTO):
    version: int = Field(ge=1)

class WorkspaceRelListDTO(WorkspaceDTO):
    shopping_lists: list['ShoppingListRelItemDTO'] | None
    role: Role | None = None


class WorkspaceRelUserDTO(WorkspaceDTO):
    members_roles: list['WorkspaceMembersRelUserDTO'] | None
