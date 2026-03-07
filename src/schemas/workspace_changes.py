import uuid
from typing import Literal,  Union

from pydantic import BaseModel, Field, RootModel

from schemas.list_items import ListItemCreateDTO, ListItemPatchDTO
from schemas.shopping_lists import ShoppingListCreateDTO, ShoppingListPatchDTO
from schemas.types import CreateOperation, DeleteOperation, OperationBase, PatchOperation
from schemas.workspaces import WorkspaceCreateDTO, WorkspacePatchDTO


class WorkspaceCreateOperation(CreateOperation[WorkspaceCreateDTO]):
    op: Literal['workspace.create']


class WorkspacePatchOperation(PatchOperation[WorkspacePatchDTO]):
    op: Literal['workspace.patch']


class WorkspaceDeleteOperation(DeleteOperation):
    op: Literal['workspace.delete']


class ShoppingListCreateOperation(CreateOperation[ShoppingListCreateDTO]):
    op: Literal['shopping_list.create']


class ShoppingListPatchOperation(PatchOperation[ShoppingListPatchDTO]):
    op: Literal['shopping_list.patch']


class ShoppingListDeleteOperation(DeleteOperation):
    op: Literal['shopping_list.delete']


class ListItemCreateOperation(CreateOperation[ListItemCreateDTO]):
    op: Literal['list_item.create']


class ListItemPatchOperation(PatchOperation[ListItemPatchDTO]):
    op: Literal['list_item.patch']


class ListItemDeleteOperation(DeleteOperation):
    op: Literal['list_item.delete']


class UnionOperation(RootModel):
    root: Union[
        WorkspaceCreateOperation,
        WorkspacePatchOperation,
        WorkspaceDeleteOperation,
        ShoppingListCreateOperation,
        ShoppingListPatchDTO,
        ShoppingListDeleteOperation,
        ListItemCreateOperation,
        ListItemPatchOperation,
        ListItemDeleteOperation,
    ] = Field(discriminator='op')



class WorkspaceChangeCreateDTO(BaseModel):
    workspace_id: uuid.UUID
    workspace_version: int = Field(ge=1)
    changes: list[UnionOperation]


class WorkspaceSyncResultDTO(BaseModel):
    workspace_id: uuid.UUID
    accepted: bool
    changes: list[UnionOperation]
