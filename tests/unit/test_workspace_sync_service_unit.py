import sys
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from uuid_utils import uuid7

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.append(str(SRC_PATH))

from core.enums import Role
from services.workspace_sync import WorkspaceSyncService
from services.exceptions import DuplicateWorkspaceSyncPayload
from schemas.workspace_changes import (
    ListItemsCreateOperation,
    WorkspaceChangeCreateDTO,
    WorkspaceVersionDTO,
    UnionOperation,
    WorkspacePatchOperation,
)
from schemas.list_items import ListItemCreateDTO, ListItemsCreateDTO
from schemas.workspaces import WorkspacePatchDTO


class DummyCrudService:
    def __init__(self) -> None:
        self.create = AsyncMock()
        self.create_deferred = AsyncMock()
        self.patch = AsyncMock()
        self.delete = AsyncMock()
        self.editable_workspace_ids: set[uuid.UUID] | None = None

    def set_editable_workspace_ids(self, editable_workspace_ids: set[uuid.UUID] | None) -> None:
        self.editable_workspace_ids = editable_workspace_ids


def _uuid7() -> uuid.UUID:
    return uuid.UUID(str(uuid7()))


def _build_uow(
        *,
        members: list[SimpleNamespace],
        workspaces: list[SimpleNamespace] | None = None,
        compare_versions_result: dict[uuid.UUID, int] | None = None,
        changes_result: list[WorkspaceChangeCreateDTO] | None = None,
) -> SimpleNamespace:
    uow = SimpleNamespace()
    uow.log = MagicMock()
    uow.set_defer_flush = MagicMock()
    uow.workspace_members = SimpleNamespace(
        get_all=AsyncMock(return_value=members),
    )
    uow.workspaces = SimpleNamespace(
        get_all=AsyncMock(return_value=workspaces or []),
        compare_and_bump_versions=AsyncMock(return_value=compare_versions_result or {}),
    )
    uow.workspace_changes = SimpleNamespace(
        add_all=AsyncMock(),
        get_since_versions=AsyncMock(return_value=changes_result or []),
    )
    return uow


def _wire_dummy_services(sync_service: WorkspaceSyncService) -> DummyCrudService:
    workspace_service = DummyCrudService()
    shopping_list_service = DummyCrudService()
    list_item_service = DummyCrudService()
    sync_service._workspaces_service = workspace_service
    sync_service._shopping_lists_service = shopping_list_service
    sync_service._list_items_service = list_item_service
    sync_service._service_map = {
        "workspace": workspace_service,
        "shopping_list": shopping_list_service,
        "list_items": list_item_service,
    }
    return workspace_service


@pytest.mark.asyncio
async def test_workspace_sync_push_duplicate_workspace_ids_raises() -> None:
    user_id = _uuid7()
    workspace_id = _uuid7()
    uow = _build_uow(members=[])
    sync_service = WorkspaceSyncService(uow)
    _wire_dummy_services(sync_service)
    change = WorkspaceChangeCreateDTO(
        workspace_id=workspace_id,
        workspace_version=1,
        changes=[],
    )

    raised = False
    try:
        await sync_service.push_changes(user_id, [change, change])
    except DuplicateWorkspaceSyncPayload:
        raised = True
    assert raised is True


@pytest.mark.asyncio
async def test_workspace_sync_push_viewer_rejected() -> None:
    user_id = _uuid7()
    workspace_id = _uuid7()
    members = [SimpleNamespace(workspace_id=workspace_id, role=Role.viewer)]
    workspaces = [SimpleNamespace(id=workspace_id, version=1)]
    uow = _build_uow(
        members=members,
        workspaces=workspaces,
        compare_versions_result={},
    )
    sync_service = WorkspaceSyncService(uow)
    workspace_service = _wire_dummy_services(sync_service)

    patch_op = WorkspacePatchOperation(
        data=WorkspacePatchDTO(id=workspace_id, name="viewer-updated"),
    )
    change = WorkspaceChangeCreateDTO(
        workspace_id=workspace_id,
        workspace_version=1,
        changes=[UnionOperation(root=patch_op)],
    )

    result = await sync_service.push_changes(user_id, [change])

    assert result[0].workspace_id == workspace_id
    assert result[0].accepted is False
    assert workspace_service.patch.await_count == 0
    assert uow.workspace_changes.add_all.await_count == 0


@pytest.mark.asyncio
async def test_workspace_sync_push_editor_applies_and_bumps() -> None:
    user_id = _uuid7()
    workspace_id = _uuid7()
    members = [SimpleNamespace(workspace_id=workspace_id, role=Role.editor)]
    workspaces = [SimpleNamespace(id=workspace_id, version=1)]
    bumped_versions = {workspace_id: 2}
    uow = _build_uow(
        members=members,
        workspaces=workspaces,
        compare_versions_result=bumped_versions,
    )
    sync_service = WorkspaceSyncService(uow)
    workspace_service = _wire_dummy_services(sync_service)

    patch_data = WorkspacePatchDTO(id=workspace_id, name="sync-updated")
    patch_op = WorkspacePatchOperation(data=patch_data)
    change = WorkspaceChangeCreateDTO(
        workspace_id=workspace_id,
        workspace_version=1,
        changes=[UnionOperation(root=patch_op)],
    )

    result = await sync_service.push_changes(user_id, [change])

    assert result[0].workspace_id == workspace_id
    assert result[0].accepted is True
    workspace_service.patch.assert_awaited_once_with(patch_data, user_id)
    uow.workspace_changes.add_all.assert_awaited_once()
    added_changes = uow.workspace_changes.add_all.call_args[0][0]
    assert len(added_changes) == 1
    assert added_changes[0].workspace_version == 2


@pytest.mark.asyncio
async def test_workspace_sync_push_grouped_item_create_uses_batch_method() -> None:
    user_id = _uuid7()
    workspace_id = _uuid7()
    list_id = _uuid7()
    item_id = _uuid7()
    members = [SimpleNamespace(workspace_id=workspace_id, role=Role.editor)]
    workspaces = [SimpleNamespace(id=workspace_id, version=1)]
    bumped_versions = {workspace_id: 2}
    uow = _build_uow(
        members=members,
        workspaces=workspaces,
        compare_versions_result=bumped_versions,
    )
    sync_service = WorkspaceSyncService(uow)
    _wire_dummy_services(sync_service)
    list_item_service = sync_service._list_items_service

    item_data = ListItemCreateDTO(
        id=item_id,
        list_id=list_id,
        name="milk",
        quantity=1,
        unit="pcs",
        category="dairy",
        is_purchased=False,
    )
    create_op = ListItemsCreateOperation(
        data=ListItemsCreateDTO(
            list_id=list_id,
            items=[item_data],
        ),
    )
    change = WorkspaceChangeCreateDTO(
        workspace_id=workspace_id,
        workspace_version=1,
        changes=[UnionOperation(root=create_op)],
    )

    result = await sync_service.push_changes(user_id, [change])

    assert result[0].accepted is True
    list_item_service.create_deferred.assert_awaited_once_with(
        ListItemsCreateDTO(
            list_id=list_id,
            items=[item_data],
        ),
        user_id,
    )


@pytest.mark.asyncio
async def _test_workspace_sync_pull_includes_missing_versions() -> None:
    user_id = _uuid7()
    workspace_id = _uuid7()
    extra_workspace_id = _uuid7()
    members = [
        SimpleNamespace(workspace_id=workspace_id, role=Role.editor),
        SimpleNamespace(workspace_id=extra_workspace_id, role=Role.viewer),
    ]
    expected_changes = [
        WorkspaceChangeCreateDTO(
            workspace_id=workspace_id,
            workspace_version=1,
            changes=[],
        )
    ]
    uow = _build_uow(
        members=members,
        changes_result=expected_changes,
    )
    sync_service = WorkspaceSyncService(uow)

    versions = [WorkspaceVersionDTO(workspace_id=workspace_id, workspace_version=3)]
    changes = await sync_service.pull_changes(user_id, versions)

    assert changes == expected_changes
    uow.workspace_changes.get_since_versions.assert_awaited_once_with(
        {workspace_id: 3, extra_workspace_id: 0}
    )
