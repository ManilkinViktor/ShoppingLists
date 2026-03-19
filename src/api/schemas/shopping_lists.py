import uuid

from pydantic import BaseModel, Field

from api.schemas.list_items import ListItemCreateRequestDTO
from api.schemas.workspaces import WorkspaceVersionRequestDTO
from schemas.mixins import UUIDMixinDTO
from core.constants import FieldConstraints


class ShoppingListCreateRequestDTO(UUIDMixinDTO, WorkspaceVersionRequestDTO):
    workspace_id: uuid.UUID
    name: str = Field(min_length=1, max_length=FieldConstraints.base_len)
    description: str | None = Field(max_length=FieldConstraints.base_len)


class ShoppingListCreateWithItemsDTO(ShoppingListCreateRequestDTO):
    items: list[ListItemCreateRequestDTO] = Field(default_factory=list)


class ShoppingListPatchRequestDTO(WorkspaceVersionRequestDTO):
    name: str | None = Field(default=None, min_length=1, max_length=FieldConstraints.base_len)
    description: str | None = Field(default=None, max_length=FieldConstraints.base_len)


class ShoppingListDeleteRequestDTO(WorkspaceVersionRequestDTO):
    pass
