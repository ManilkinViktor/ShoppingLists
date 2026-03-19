import uuid

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import WorkspaceChangesOrm
from schemas.workspace_changes import WorkspaceChangeCreateDTO


class WorkspaceChangesRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _is_flush_deferred(self) -> bool:
        return bool(self._session.info.get('defer_flush'))

    async def _flush_if_needed(self) -> None:
        if not self._is_flush_deferred():
            await self._session.flush()

    async def add_all(self, changes: list[WorkspaceChangeCreateDTO]) -> None:
        for workspace_change in changes:
            payload = [change.model_dump(mode='json') for change in workspace_change.changes]
            self._session.add(
                WorkspaceChangesOrm(
                    workspace_id=workspace_change.workspace_id,
                    workspace_version=workspace_change.workspace_version,
                    change={'changes': payload},
                )
            )
        await self._flush_if_needed()

    async def get_since_versions(
        self,
        workspace_versions: dict[uuid.UUID, int],
    ) -> list[WorkspaceChangeCreateDTO]:
        if not workspace_versions:
            return []

        conditions = [
            and_(
                WorkspaceChangesOrm.workspace_id == workspace_id,
                WorkspaceChangesOrm.workspace_version > version,
            )
            for workspace_id, version in workspace_versions.items()
        ]
        query = (
            select(WorkspaceChangesOrm)
            .where(or_(*conditions))
            .order_by(WorkspaceChangesOrm.workspace_id, WorkspaceChangesOrm.workspace_version)
        )
        result = await self._session.execute(query)
        rows = result.scalars().all()

        return [
            WorkspaceChangeCreateDTO.model_validate(
                {
                    'workspace_id': row.workspace_id,
                    'workspace_version': row.workspace_version,
                    'changes': row.change.get('changes', []),
                }
            )
            for row in rows
        ]
