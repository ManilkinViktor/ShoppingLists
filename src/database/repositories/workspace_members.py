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
