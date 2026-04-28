import uuid

from pydantic import Field

from api.schemas.workspaces import WorkspaceVersionRequestDTO
from core.constants import FieldConstraints
from schemas.list_items import ListItemCreateDTO, ListItemPatchDTO
from schemas.mixins import UUIDMixinDTO


class ShoppingListCreateRequestDTO(UUIDMixinDTO, WorkspaceVersionRequestDTO):
    workspace_id: uuid.UUID
    name: str = Field(min_length=1, max_length=FieldConstraints.BASE_LEN)
    description: str | None = Field(max_length=FieldConstraints.DESCRIPTION_LEN)


class ShoppingListCreateWithItemsDTO(ShoppingListCreateRequestDTO):
    items: list[ListItemCreateDTO] = Field(default_factory=list)


class ShoppingListPatchRequestDTO(WorkspaceVersionRequestDTO):
    name: str | None = Field(default=None, min_length=1, max_length=FieldConstraints.BASE_LEN)
    description: str | None = Field(default=None, max_length=FieldConstraints.DESCRIPTION_LEN)
    create_items: list[ListItemCreateDTO] = Field(default_factory=list)
    patch_items: list[ListItemPatchDTO] = Field(default_factory=list)
    delete_items_ids: list[uuid.UUID] = Field(default_factory=list)


class ShoppingListDeleteRequestDTO(WorkspaceVersionRequestDTO):
    pass
