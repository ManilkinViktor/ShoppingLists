from sqlalchemy.ext.asyncio import AsyncSession

from database.models import WorkspaceInvitesOrm
from database.repositories.base import BaseRepository
from schemas.workspace_invites import WorkspaceInviteDTO, WorkspaceInviteCreateDTO


class WorkspaceInvitesRepository(
    BaseRepository[
        WorkspaceInvitesOrm,
        WorkspaceInviteCreateDTO,
        WorkspaceInviteDTO
    ]
):

    def __init__(self, _session: AsyncSession) -> None:
        super().__init__(
            _session,
            _model=WorkspaceInvitesOrm,
            _add_dto=WorkspaceInviteDTO,
            _dto=WorkspaceInviteDTO
        )
