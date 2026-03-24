import sys
import uuid
from pathlib import Path

import pytest
from uuid_utils import uuid7

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.append(str(SRC_PATH))

from conftest import session_factory
from core.enums import Role
from database.repositories.list_items import ListItemsRepository
from database.repositories.shopping_lists import ShoppingListsRepository
from database.repositories.users import UsersRepository
from database.repositories.workspace_members import WorkspaceMembersRepository
from database.repositories.workspaces import WorkspacesRepository
from schemas.list_items import ListItemCreateDTO
from schemas.shopping_lists import ShoppingListCreateDTO
from schemas.users import UserCreateAuthDTO
from schemas.workspace_members import WorkspaceMemberCreateDTO
from schemas.workspaces import WorkspaceCreateDTO


@pytest.mark.asyncio
async def test_get_workspace_with_lists_hides_soft_deleted_relations() -> None:
    user_id = uuid.UUID(str(uuid7()))
    workspace_id = uuid.UUID(str(uuid7()))
    active_list_id = uuid.UUID(str(uuid7()))
    deleted_list_id = uuid.UUID(str(uuid7()))
    active_item_id = uuid.UUID(str(uuid7()))
    deleted_item_id = uuid.UUID(str(uuid7()))
    email = f"soft-delete-workspace-{workspace_id}@example.com"

    try:
        async with session_factory() as session:
            users = UsersRepository(session)
            workspaces = WorkspacesRepository(session)
            workspace_members = WorkspaceMembersRepository(session)
            shopping_lists = ShoppingListsRepository(session)
            list_items = ListItemsRepository(session)

            await users.add(
                UserCreateAuthDTO(
                    id=user_id,
                    name="soft-delete-user",
                    email=email,
                    hashed_password="hashed",
                )
            )
            await workspaces.add(
                WorkspaceCreateDTO(
                    id=workspace_id,
                    name="workspace",
                    description=None,
                    owner_id=user_id,
                )
            )
            await workspace_members.add(
                WorkspaceMemberCreateDTO(
                    workspace_id=workspace_id,
                    user_id=user_id,
                    role=Role.editor,
                )
            )
            await shopping_lists.add(
                ShoppingListCreateDTO(
                    id=active_list_id,
                    workspace_id=workspace_id,
                    name="active-list",
                    description=None,
                    created_by=user_id,
                )
            )
            await shopping_lists.add(
                ShoppingListCreateDTO(
                    id=deleted_list_id,
                    workspace_id=workspace_id,
                    name="deleted-list",
                    description=None,
                    created_by=user_id,
                )
            )
            await list_items.add(
                ListItemCreateDTO(
                    id=active_item_id,
                    list_id=active_list_id,
                    name="active-item",
                    quantity=1,
                    unit=None,
                    category=None,
                    is_purchased=False,
                )
            )
            await list_items.add(
                ListItemCreateDTO(
                    id=deleted_item_id,
                    list_id=active_list_id,
                    name="deleted-item",
                    quantity=1,
                    unit=None,
                    category=None,
                    is_purchased=False,
                )
            )
            await list_items.delete(deleted_item_id)
            await shopping_lists.delete(deleted_list_id)
            await session.commit()

        async with session_factory() as session:
            workspaces = WorkspacesRepository(session)
            loaded = await workspaces.get_workspace_with_lists(workspace_id)

            assert loaded is not None
            assert loaded.id == workspace_id
            assert loaded.shopping_lists is not None
            assert [shopping_list.id for shopping_list in loaded.shopping_lists] == [active_list_id]
            assert loaded.shopping_lists[0].items is not None
            assert [item.id for item in loaded.shopping_lists[0].items] == [active_item_id]
    finally:
        async with session_factory() as session:
            users = UsersRepository(session)
            workspaces = WorkspacesRepository(session)
            await workspaces.delete(workspace_id)
            await users.delete(user_id)
            await session.commit()


@pytest.mark.asyncio
async def test_get_list_with_items_hides_soft_deleted_items_and_deleted_list() -> None:
    user_id = uuid.UUID(str(uuid7()))
    workspace_id = uuid.UUID(str(uuid7()))
    list_id = uuid.UUID(str(uuid7()))
    item_id = uuid.UUID(str(uuid7()))
    deleted_item_id = uuid.UUID(str(uuid7()))
    deleted_list_id = uuid.UUID(str(uuid7()))
    email = f"soft-delete-list-{workspace_id}@example.com"

    try:
        async with session_factory() as session:
            users = UsersRepository(session)
            workspaces = WorkspacesRepository(session)
            shopping_lists = ShoppingListsRepository(session)
            list_items = ListItemsRepository(session)

            await users.add(
                UserCreateAuthDTO(
                    id=user_id,
                    name="soft-delete-list-user",
                    email=email,
                    hashed_password="hashed",
                )
            )
            await workspaces.add(
                WorkspaceCreateDTO(
                    id=workspace_id,
                    name="workspace",
                    description=None,
                    owner_id=user_id,
                )
            )
            await shopping_lists.add(
                ShoppingListCreateDTO(
                    id=list_id,
                    workspace_id=workspace_id,
                    name="active-list",
                    description=None,
                    created_by=user_id,
                )
            )
            await shopping_lists.add(
                ShoppingListCreateDTO(
                    id=deleted_list_id,
                    workspace_id=workspace_id,
                    name="deleted-list",
                    description=None,
                    created_by=user_id,
                )
            )
            await list_items.add(
                ListItemCreateDTO(
                    id=item_id,
                    list_id=list_id,
                    name="active-item",
                    quantity=1,
                    unit=None,
                    category=None,
                    is_purchased=False,
                )
            )
            await list_items.add(
                ListItemCreateDTO(
                    id=deleted_item_id,
                    list_id=list_id,
                    name="deleted-item",
                    quantity=1,
                    unit=None,
                    category=None,
                    is_purchased=False,
                )
            )
            await list_items.delete(deleted_item_id)
            await shopping_lists.delete(deleted_list_id)
            await session.commit()

        async with session_factory() as session:
            shopping_lists = ShoppingListsRepository(session)

            loaded_active = await shopping_lists.get_list_with_items(list_id)
            loaded_deleted = await shopping_lists.get_list_with_items(deleted_list_id)

            assert loaded_active is not None
            assert loaded_active.items is not None
            assert [item.id for item in loaded_active.items] == [item_id]
            assert loaded_deleted is None
    finally:
        async with session_factory() as session:
            users = UsersRepository(session)
            workspaces = WorkspacesRepository(session)
            await workspaces.delete(workspace_id)
            await users.delete(user_id)
            await session.commit()
