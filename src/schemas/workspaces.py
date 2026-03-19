import uuid
from typing import TYPE_CHECKING

from pydantic import Field

from core.constants import FieldConstraints
from core.enums import Role
from schemas.mixins import UUIDMixinDTO, TimeStampMixinDTO

if TYPE_CHECKING:
    from schemas.shopping_lists import ShoppingListRelItemDTO
    from schemas.workspace_members import WorkspaceMembersRelUserDTO


class WorkspaceCreateDTO(UUIDMixinDTO):
    name: str = Field(min_length=1, max_length=FieldConstraints.BASE_LEN)
    description: str | None = Field(max_length=FieldConstraints.BASE_LEN)
    owner_id: uuid.UUID | None = None


class WorkspacePatchDTO(UUIDMixinDTO):
    name: str | None = Field(default=None, min_length=1, max_length=FieldConstraints.BASE_LEN)
    description: str | None = Field(default=None, max_length=FieldConstraints.BASE_LEN)


class WorkspaceDTO(WorkspaceCreateDTO, TimeStampMixinDTO):
    version: int = Field(ge=1)


class WorkspaceRelListDTO(WorkspaceDTO):
    shopping_lists: list['ShoppingListRelItemDTO'] | None
    role: Role | None = None


class WorkspaceRelUserDTO(WorkspaceDTO):
    members_roles: list['WorkspaceMembersRelUserDTO'] | None
