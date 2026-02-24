import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database.models import WorkspacesOrm, ShoppingListsOrm, WorkspaceMembersOrm
from database.models.workspace_members import Role
from schemas.workspaces import WorkspaceDTO, WorkspaceAddDTO, WorkspaceRelListDTO
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
            _model=WorkspacesOrm, _add_dto=WorkspaceAddDTO, _dto=WorkspaceDTO
        )


    async def get_workspace_with_lists(self, workspace_id: uuid.UUID) -> WorkspaceRelListDTO | None:
        """Return workspace with lists together list's items"""
        query = (
            select(WorkspacesOrm)
            .where(WorkspacesOrm.id == workspace_id)
            .options(
                selectinload(WorkspacesOrm.shopping_lists)
                .selectinload(ShoppingListsOrm.items)
            )
        )
        result = await self._session.execute(query)
        workspace: WorkspacesOrm = result.scalar_one_or_none()
        return WorkspaceRelListDTO.model_validate(workspace, from_attributes=True) if workspace else None

    async def get_accessible_user_workspaces_with_lists(self, user_id: uuid.UUID) -> list[tuple[WorkspaceRelListDTO, Role]]:
        """Return accessible users workspaces with role and list together list's items"""
        query = (
            select(WorkspacesOrm, WorkspaceMembersOrm.role.label('role'))
            .join(WorkspaceMembersOrm, WorkspacesOrm.id == WorkspaceMembersOrm.workspace_id)
            .where(WorkspaceMembersOrm.user_id == user_id)
            .options(
                selectinload(WorkspacesOrm.shopping_lists)
                .selectinload(ShoppingListsOrm.items)
            )

        )
        result = await self._session.execute(query)
        accessible_workspaces: list[tuple[WorkspaceRelListDTO, Role]] = []
        for row in result:
            workspace: WorkspacesOrm = row[0]
            role: Role = row.role
            accessible_workspaces.append((WorkspaceRelListDTO.model_validate(workspace), role))


        return accessible_workspaces
