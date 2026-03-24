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
from database.repositories.workspaces import WorkspacesRepository
from schemas.workspaces import WorkspaceCreateDTO


@pytest.mark.asyncio
async def test_compare_and_bump_ignores_soft_deleted_workspace() -> None:
    workspace_id = uuid.UUID(str(uuid7()))

    try:
        async with session_factory() as session:
            repository = WorkspacesRepository(session)
            await repository.add(
                WorkspaceCreateDTO(
                    id=workspace_id,
                    name="deleted-workspace",
                    description=None,
                    owner_id=None,
                )
            )
            await session.commit()

        async with session_factory() as session:
            repository = WorkspacesRepository(session)
            deleted = await repository.delete(workspace_id)
            await session.commit()
            assert deleted is True

        async with session_factory() as session:
            repository = WorkspacesRepository(session)
            assert await repository.compare_and_bump_version(workspace_id, 1) is False
            assert await repository.compare_and_bump_versions({workspace_id: 1}) == {}
    finally:
        async with session_factory() as session:
            repository = WorkspacesRepository(session)
            await repository.delete(workspace_id)
            await session.commit()
