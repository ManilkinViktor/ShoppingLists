import uuid

from sqlalchemy import select, tuple_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, with_loader_criteria

from core.enums import Role
from database.models import WorkspacesOrm, ShoppingListsOrm, WorkspaceMembersOrm, ListItemsOrm
from database.repositories.base import BaseRepository
from schemas.workspaces import WorkspaceDTO, WorkspaceCreateDTO, WorkspaceRelListDTO


class WorkspacesRepository(
    BaseRepository[
        WorkspacesOrm,
        WorkspaceCreateDTO,
        WorkspaceDTO
    ]):

    def __init__(self, _session: AsyncSession) -> None:
        super().__init__(
            _session,
            _model=WorkspacesOrm, _add_dto=WorkspaceCreateDTO, _dto=WorkspaceDTO
        )

    async def get_workspace_with_lists(self, workspace_id: uuid.UUID) -> WorkspaceRelListDTO | None:
        """Return workspace with lists together list's items"""
        query = (
            select(WorkspacesOrm)
            .where(WorkspacesOrm.id == workspace_id)
            .where(WorkspacesOrm.deleted_at.is_(None))
            .options(
                selectinload(WorkspacesOrm.shopping_lists).selectinload(ShoppingListsOrm.items),
                with_loader_criteria(
                    ShoppingListsOrm,
                    ShoppingListsOrm.deleted_at.is_(None),
                    include_aliases=True,
                ),
                with_loader_criteria(
                    ListItemsOrm,
                    ListItemsOrm.deleted_at.is_(None),
                    include_aliases=True,
                ),
            )
        )
        result = await self._session.execute(query)
        workspace: WorkspacesOrm = result.scalar_one_or_none()
        return WorkspaceRelListDTO.model_validate(workspace, from_attributes=True) if workspace else None

    async def get_accessible_user_workspaces(
            self,
            user_id: uuid.UUID,
    ) -> list[WorkspaceDTO]:
        """Return accessible users workspaces without nested lists/items."""
        query = (
            select(WorkspacesOrm)
            .join(WorkspaceMembersOrm, WorkspacesOrm.id == WorkspaceMembersOrm.workspace_id)
            .where(WorkspaceMembersOrm.user_id == user_id)
        )
        if hasattr(WorkspacesOrm, "deleted_at"):
            query = query.where(WorkspacesOrm.deleted_at.is_(None))
        result = await self._session.execute(query)
        workspaces = result.scalars().all()
        return [
            WorkspaceDTO.model_validate(workspace, from_attributes=True)
            for workspace in workspaces
        ]

    async def get_accessible_user_workspaces_with_lists(
            self,
            user_id: uuid.UUID,
    ) -> list[WorkspaceRelListDTO]:
        """Return accessible users workspaces with role and list together list's items"""
        query = (
            select(WorkspacesOrm, WorkspaceMembersOrm.role.label('role'))
            .join(WorkspaceMembersOrm, WorkspacesOrm.id == WorkspaceMembersOrm.workspace_id)
            .where(WorkspaceMembersOrm.user_id == user_id)
            .where(WorkspacesOrm.deleted_at.is_(None))
            .options(
                selectinload(WorkspacesOrm.shopping_lists).selectinload(ShoppingListsOrm.items),
                with_loader_criteria(
                    ShoppingListsOrm,
                    ShoppingListsOrm.deleted_at.is_(None),
                    include_aliases=True,
                ),
                with_loader_criteria(
                    ListItemsOrm,
                    ListItemsOrm.deleted_at.is_(None),
                    include_aliases=True,
                ),
            )

        )
        result = await self._session.execute(query)
        accessible_workspaces: list[WorkspaceRelListDTO] = []
        for row in result:
            workspace: WorkspacesOrm = row[0]
            role: Role = row.role
            workspace_dto = WorkspaceRelListDTO.model_validate(workspace, from_attributes=True)
            accessible_workspaces.append(workspace_dto.model_copy(update={'role': role}))

        return accessible_workspaces

    async def compare_and_bump_version(self, workspace_id: uuid.UUID, expected_version: int) -> bool:
        """
        compare workspace's version.
        if workspace's versions are equal bump workspace version.
        return: was change
        """
        stmt = (
            update(WorkspacesOrm)
            .where(WorkspacesOrm.id == workspace_id, WorkspacesOrm.version == expected_version)
            .where(WorkspacesOrm.deleted_at.is_(None))
            .values(version=WorkspacesOrm.version + 1)
            .returning(WorkspacesOrm.version)
        )
        result = await self._session.execute(stmt)
        return bool(result.scalar_one_or_none())

    async def compare_and_bump_versions(
            self,
            expected_versions: dict[uuid.UUID, int],
    ) -> dict[uuid.UUID, int]:
        if not expected_versions:
            return {}

        stmt = (
            update(WorkspacesOrm)
            .where(tuple_(WorkspacesOrm.id, WorkspacesOrm.version).in_(expected_versions.items()))
            .where(WorkspacesOrm.deleted_at.is_(None))
            .values(version=WorkspacesOrm.version + 1)
            .returning(WorkspacesOrm.id, WorkspacesOrm.version)
        )
        result = await self._session.execute(stmt)
        rows = result.all()
        return {row.id: row.version for row in rows}
