import asyncio
import uuid
from pathlib import Path
import sys

from uuid_utils import uuid7


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.append(str(SRC_PATH))

from database.repositories.workspaces import WorkspacesRepository
from database.session import session_factory
from schemas.workspaces import WorkspaceCreateDTO


def test_workspaces_repository_roundtrip() -> None:
    asyncio.run(_test_workspaces_repository_roundtrip())


async def _test_workspaces_repository_roundtrip() -> None:
    workspace_id = uuid.UUID(str(uuid7()))

    try:
        async with session_factory() as session:
            repository = WorkspacesRepository(session)

            workspace_to_create = WorkspaceCreateDTO(
                id=workspace_id,
                name="integration-test-workspace",
                description="db roundtrip test",
                owner_id=None,
            )

            created = await repository.add(workspace_to_create)
            await session.commit()

            assert created.id == workspace_id
            assert created.version == 1

        async with session_factory() as session:
            repository = WorkspacesRepository(session)
            loaded = await repository.get(workspace_id)

            assert loaded is not None
            assert loaded.id == workspace_id
            assert loaded.name == "integration-test-workspace"
            assert loaded.version == 1
            assert loaded.deleted_at is None
    finally:
        async with session_factory() as session:
            repository = WorkspacesRepository(session)
            await repository.delete(workspace_id)
            await session.commit()
