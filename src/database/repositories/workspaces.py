from sqlalchemy.ext.asyncio import AsyncSession

from database.models import WorkspacesOrm
from schemas.workspaces import WorkspaceDTO
from database.repositories.base import BaseRepository

class WorkspacesRepository(
    BaseRepository[
        WorkspacesOrm,
        WorkspaceDTO,
        WorkspaceDTO
    ]):

    def __init__(self, _session: AsyncSession):
        super().__init__(
            _session,
            _model=WorkspacesOrm, _add_dto=WorkspaceDTO, _dto=WorkspaceDTO
        )

