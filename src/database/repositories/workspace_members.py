from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories.base import BaseRepository
from schemas.workspace_members import WorkspaceMemberDTO, WorkspaceMemberAddDTO
from database.models import WorkspaceMembersOrm

class WorkspaceMembersRepository(
    BaseRepository[
        WorkspaceMembersOrm,
        WorkspaceMemberAddDTO,
        WorkspaceMemberDTO
    ]
    ):

    def __init__(self, _session: AsyncSession):
        super().__init__(_session,
                         _model=WorkspaceMembersOrm, _add_dto=WorkspaceMemberDTO, _dto=WorkspaceMemberDTO)

