import uuid
from typing import Literal, Union

from pydantic import BaseModel, Field, RootModel

from schemas.list_items import (
    ListItemsCreateDTO,
    ListItemsDeleteDTO,
    ListItemsPatchDTO,
)
from schemas.shopping_lists import ShoppingListCreateDTO, ShoppingListPatchDTO
from schemas.types import CreateOperation, DeleteOperation, PatchOperation
from schemas.workspaces import WorkspaceCreateDTO, WorkspacePatchDTO


class WorkspaceCreateOperation(CreateOperation[WorkspaceCreateDTO]):
    op: Literal['workspace.create'] = 'workspace.create'


class WorkspacePatchOperation(PatchOperation[WorkspacePatchDTO]):
    op: Literal['workspace.patch'] = 'workspace.patch'


class WorkspaceDeleteOperation(DeleteOperation[uuid.UUID]):
    op: Literal['workspace.delete'] = 'workspace.delete'


class ShoppingListCreateOperation(CreateOperation[ShoppingListCreateDTO]):
    op: Literal['shopping_list.create'] = 'shopping_list.create'


class ShoppingListPatchOperation(PatchOperation[ShoppingListPatchDTO]):
    op: Literal['shopping_list.patch'] = 'shopping_list.patch'


class ShoppingListDeleteOperation(DeleteOperation[uuid.UUID]):
    op: Literal['shopping_list.delete'] = 'shopping_list.delete'


class ListItemsCreateOperation(CreateOperation[ListItemsCreateDTO]):
    op: Literal['list_items.create'] = 'list_items.create'


class ListItemsPatchOperation(PatchOperation[ListItemsPatchDTO]):
    op: Literal['list_items.patch'] = 'list_items.patch'


class ListItemsDeleteOperation(DeleteOperation[ListItemsDeleteDTO]):
    op: Literal['list_items.delete'] = 'list_items.delete'


class UnionOperation(RootModel):
    root: Union[
        WorkspaceCreateOperation,
        WorkspacePatchOperation,
        WorkspaceDeleteOperation,
        ShoppingListCreateOperation,
        ShoppingListPatchOperation,
        ShoppingListDeleteOperation,
        ListItemsCreateOperation,
        ListItemsPatchOperation,
        ListItemsDeleteOperation,
    ] = Field(discriminator='op')


class WorkspaceChangeCreateDTO(BaseModel):
    workspace_id: uuid.UUID
    workspace_version: int = Field(ge=1)
    changes: list[UnionOperation]


class WorkspaceVersionDTO(BaseModel):
    workspace_id: uuid.UUID
    workspace_version: int = Field(ge=0)


class WorkspacePushResultDTO(BaseModel):
    workspace_id: uuid.UUID
    accepted: bool


class WorkspaceSyncResultDTO(BaseModel):
    workspace_id: uuid.UUID
    accepted: bool
    changes: list[UnionOperation]
