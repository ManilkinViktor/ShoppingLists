from typing import Type

from pydantic import BaseModel


def rebuild_models() -> None:
    from schemas.workspaces import WorkspaceRelListDTO, WorkspaceRelUserDTO
    from schemas.shopping_lists import ShoppingListRelItemDTO, ShoppingListRelWorkspaceDTO
    from schemas.list_items import ListItemDTO, ListItemRelListDTO
    from schemas.users import UserDTO, UserRelWorkspaceDTO
    from schemas.workspace_members import (
        WorkspaceMemberRelWorkspaceDTO,
        WorkspaceMembersRelUserDTO,
    )

    models: list[Type[BaseModel]] = [
        WorkspaceRelListDTO,
        WorkspaceRelUserDTO,
        ShoppingListRelItemDTO,
        ShoppingListRelWorkspaceDTO,
        ListItemRelListDTO,
        UserRelWorkspaceDTO,
        WorkspaceMemberRelWorkspaceDTO,
        WorkspaceMembersRelUserDTO,
    ]
    types_namespace = {model.__name__: model for model in models}
    types_namespace['ListItemDTO'] = ListItemDTO
    types_namespace['UserDTO'] = UserDTO

    for model in models:
        model.model_rebuild(_types_namespace=types_namespace)


rebuild_models()
