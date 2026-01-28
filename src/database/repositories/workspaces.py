from sqlalchemy.ext.asyncio import AsyncSession

from database.models import WorkspacesOrm
from schemas.workspaces import WorkspaceDTO, WorkspaceAddDTO
from database.repositories.base import BaseRepository

class WorkspacesRepository(
    BaseRepository[
        WorkspacesOrm,
        WorkspaceAddDTO,
        WorkspaceDTO
    ]):

    def __init__(self, _session: AsyncSession):
        super().__init__(
            _session,
            _model=WorkspacesOrm, _add_dto=WorkspaceDTO, _dto=WorkspaceDTO
        )

