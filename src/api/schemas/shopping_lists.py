import uuid

from pydantic import Field

from api.schemas.list_items import ListItemCreateRequestDTO
from api.schemas.workspaces import WorkspaceVersionRequestDTO
from core.constants import FieldConstraints
from schemas.mixins import UUIDMixinDTO


class ShoppingListCreateRequestDTO(UUIDMixinDTO, WorkspaceVersionRequestDTO):
    workspace_id: uuid.UUID
    name: str = Field(min_length=1, max_length=FieldConstraints.BASE_LEN)
    description: str | None = Field(max_length=FieldConstraints.DESCRIPTION_LEN)


class ShoppingListCreateWithItemsDTO(ShoppingListCreateRequestDTO):
    items: list[ListItemCreateRequestDTO] = Field(default_factory=list)


class ShoppingListPatchRequestDTO(WorkspaceVersionRequestDTO):
    name: str | None = Field(default=None, min_length=1, max_length=FieldConstraints.BASE_LEN)
    description: str | None = Field(default=None, max_length=FieldConstraints.DESCRIPTION_LEN)


class ShoppingListDeleteRequestDTO(WorkspaceVersionRequestDTO):
    pass
