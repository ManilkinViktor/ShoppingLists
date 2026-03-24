from uuid import UUID

from sqlalchemy import delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import WorkspaceMembersOrm
from database.repositories.base import BaseRepository
from schemas.workspace_members import WorkspaceMemberDTO, WorkspaceMemberCreateDTO


class WorkspaceMembersRepository(
    BaseRepository[
        WorkspaceMembersOrm,
        WorkspaceMemberCreateDTO,
        WorkspaceMemberDTO
    ]
):

    def __init__(self, _session: AsyncSession) -> None:
        super().__init__(_session,
                         _model=WorkspaceMembersOrm, _add_dto=WorkspaceMemberDTO, _dto=WorkspaceMemberDTO)

    async def delete_by(self, workspace_id: UUID, user_id: UUID) -> bool:
        stmt = sa_delete(WorkspaceMembersOrm).where(
            (WorkspaceMembersOrm.workspace_id == workspace_id) &
            (WorkspaceMembersOrm.user_id == user_id)
        )
        result = await self._session.execute(stmt)
        await self._flush_if_needed()
        return bool(result.rowcount)
