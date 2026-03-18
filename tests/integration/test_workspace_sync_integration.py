import pytest
from pathlib import Path
import sys
import uuid

from uuid_utils import uuid7


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.append(str(SRC_PATH))

from database.uow import UnitOfWork
from core.enums import Role
from services.workspace_sync import WorkspaceSyncService
from schemas.users import UserCreateAuthDTO
from schemas.workspaces import WorkspaceCreateDTO, WorkspacePatchDTO
from schemas.workspace_members import WorkspaceMemberCreateDTO
from schemas.workspace_changes import (
    WorkspaceChangeCreateDTO,
    WorkspaceVersionDTO,
    UnionOperation,
    WorkspacePatchOperation,
)
from conftest import session_factory


@pytest.mark.asyncio
async def test_workspace_sync_push_editor() -> None:
    user_id = uuid.UUID(str(uuid7()))
    workspace_id = uuid.UUID(str(uuid7()))
    email = f"sync-editor-{workspace_id}@example.com"

    try:
        async with session_factory() as session:
            uow = UnitOfWork(session)
            await uow.users.add(
                UserCreateAuthDTO(
                    id=user_id,
                    name="sync-editor",
                    email=email,
                    hashed_password="hashed",
                )
            )
            await uow.workspaces.add(
                WorkspaceCreateDTO(
                    id=workspace_id,
                    name="sync-workspace",
                    description=None,
                    owner_id=user_id,
                )
            )
            await uow.workspace_members.add(
                WorkspaceMemberCreateDTO(
                    workspace_id=workspace_id,
                    user_id=user_id,
                    role=Role.editor,
                )
            )
            await uow.commit()

        async with session_factory() as session:
            uow = UnitOfWork(session)
            sync_service = WorkspaceSyncService(uow)
            patch_op = WorkspacePatchOperation(
                op="workspace.patch",
                data=WorkspacePatchDTO(id=workspace_id, name="sync-updated"),
            )
            change = WorkspaceChangeCreateDTO(
                workspace_id=workspace_id,
                workspace_version=1,
                changes=[UnionOperation(root=patch_op)],
            )

            result = await sync_service.push_changes(user_id, [change])

            assert result[0].workspace_id == workspace_id
            assert result[0].accepted is True

            updated = await uow.workspaces.get(workspace_id)
            await uow.commit()
            assert updated is not None
            assert updated.name == "sync-updated"
            assert updated.version == 2

    finally:
        async with session_factory() as session:
            uow = UnitOfWork(session)
            await uow.workspaces.delete(workspace_id)
            await uow.users.delete(user_id)
            await uow.commit()


@pytest.mark.asyncio
async def test_workspace_sync_push_viewer_rejected() -> None:
    user_id = uuid.UUID(str(uuid7()))
    workspace_id = uuid.UUID(str(uuid7()))
    email = f"sync-viewer-{workspace_id}@example.com"

    try:
        async with session_factory() as session:
            uow = UnitOfWork(session)
            await uow.users.add(
                UserCreateAuthDTO(
                    id=user_id,
                    name="sync-viewer",
                    email=email,
                    hashed_password="hashed",
                )
            )
            await uow.workspaces.add(
                WorkspaceCreateDTO(
                    id=workspace_id,
                    name="viewer-workspace",
                    description=None,
                    owner_id=user_id,
                )
            )
            await uow.workspace_members.add(
                WorkspaceMemberCreateDTO(
                    workspace_id=workspace_id,
                    user_id=user_id,
                    role=Role.viewer,
                )
            )
            await uow.commit()

        async with session_factory() as session:
            uow = UnitOfWork(session)
            sync_service = WorkspaceSyncService(uow)
            patch_op = WorkspacePatchOperation(
                op="workspace.patch",
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

            loaded = await uow.workspaces.get(workspace_id)
            await uow.commit()
            assert loaded is not None
            assert loaded.name == "viewer-workspace"
            assert loaded.version == 1
    finally:
        async with session_factory() as session:
            uow = UnitOfWork(session)
            await uow.workspaces.delete(workspace_id)
            await uow.users.delete(user_id)
            await uow.commit()

@pytest.mark.asyncio
async def test_workspace_sync_pull_returns_missing_versions() -> None:
    user_id = uuid.UUID(str(uuid7()))
    workspace_id = uuid.UUID(str(uuid7()))
    email = f"sync-pull-{workspace_id}@example.com"

    try:
        async with session_factory() as session:
            uow = UnitOfWork(session)
            await uow.users.add(
                UserCreateAuthDTO(
                    id=user_id,
                    name="sync-pull",
                    email=email,
                    hashed_password="hashed",
                )
            )
            await uow.workspaces.add(
                WorkspaceCreateDTO(
                    id=workspace_id,
                    name="pull-workspace",
                    description=None,
                    owner_id=user_id,
                )
            )
            await uow.workspace_members.add(
                WorkspaceMemberCreateDTO(
                    workspace_id=workspace_id,
                    user_id=user_id,
                    role=Role.editor,
                )
            )
            await uow.workspace_changes.add_all(
                [
                    WorkspaceChangeCreateDTO(
                        workspace_id=workspace_id,
                        workspace_version=2,
                        changes=[
                            UnionOperation(
                                root=WorkspacePatchOperation(
                                    op="workspace.patch",
                                    data=WorkspacePatchDTO(id=workspace_id, name="pull-updated"),
                                )
                            )
                        ],
                    )
                ]
            )
            await uow.commit()

        async with session_factory() as session:
            uow = UnitOfWork(session)
            sync_service = WorkspaceSyncService(uow)
            versions = [WorkspaceVersionDTO(workspace_id=workspace_id, workspace_version=0)]
            changes = await sync_service.pull_changes(user_id, versions)

            assert len(changes) == 1
            assert changes[0].workspace_id == workspace_id
            assert changes[0].workspace_version == 2
            assert len(changes[0].changes) == 1
    finally:
        async with session_factory() as session:
            uow = UnitOfWork(session)
            await uow.workspaces.delete(workspace_id)
            await uow.users.delete(user_id)
            await uow.commit()
