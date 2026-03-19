from uuid import UUID

from core.enums import Role
from database.uow import UnitOfWork
from schemas.workspace_changes import (
    WorkspaceCreateOperation,
    WorkspaceDeleteOperation,
    WorkspacePatchOperation,
    UnionOperation,
)
from schemas.workspace_members import WorkspaceMemberCreateDTO
from schemas.workspaces import WorkspaceCreateDTO, WorkspaceDTO, WorkspacePatchDTO, WorkspaceRelListDTO
from services.base import BaseService
from services.exceptions import ConflictUUID, EntityNotFound


class WorkspacesService(BaseService):
    def __init__(self, uow: UnitOfWork) -> None:
        super().__init__(uow)
        self._editable_workspace_ids: set[UUID] | None = None

    def set_editable_workspace_ids(self, editable_workspace_ids: set[UUID] | None) -> None:
        self._editable_workspace_ids = editable_workspace_ids

    async def _ensure_member_access(self, current_user: UUID, workspace_id: UUID) -> None:
        member = await self.uow.workspace_members.get_by(
            user_id=current_user,
            workspace_id=workspace_id,
        )
        if not member:
            self._log_warning(
                "User doesn't have access to workspace",
                extra={'workspace_id': workspace_id, 'user_id': current_user},
            )
            raise EntityNotFound(WorkspaceDTO)

    async def _ensure_editor_access(self, current_user: UUID, workspace_id: UUID) -> None:
        if self._editable_workspace_ids is not None:
            if workspace_id in self._editable_workspace_ids:
                return
            self._log_warning(
                "User doesn't have access to workspace",
                extra={'workspace_id': workspace_id, 'user_id': current_user},
            )
            raise EntityNotFound(WorkspaceDTO)

        member = await self.uow.workspace_members.get_by(
            user_id=current_user,
            workspace_id=workspace_id,
        )
        if not member or member.role != Role.editor:
            self._log_warning(
                "User doesn't have access to workspace",
                extra={'workspace_id': workspace_id, 'user_id': current_user},
            )
            raise EntityNotFound(WorkspaceDTO)

    async def _create_core(
            self,
            workspace_data: WorkspaceCreateDTO,
            current_user: UUID,
            *,
            deferred: bool,
    ) -> WorkspaceDTO | None:
        workspace_data = workspace_data.model_copy(update={'owner_id': current_user})
        found_workspace: WorkspaceDTO | None = await self.uow.workspaces.get(workspace_data.id)
        if found_workspace:
            if self._same_workspaces(found_workspace, workspace_data):
                self._log_info("Workspace already exists", extra={'workspace_id': found_workspace.id})
                return None if deferred else found_workspace
            self._log_warning("Conflict uuid: workspace with same uuid and another data exists")
            raise ConflictUUID

        membership = WorkspaceMemberCreateDTO(
            workspace_id=workspace_data.id,
            user_id=current_user,
            role=Role.editor,
        )
        if deferred:
            await self.uow.workspaces.add_deferred(workspace_data)
            await self.uow.workspace_members.add_deferred(membership)
            self._log_info("Workspace was created", extra={'workspace_id': workspace_data.id})
            return None

        workspace = await self.uow.workspaces.add(workspace_data)
        await self.uow.workspace_members.add(membership)
        self._log_info("Workspace was created", extra={'workspace_id': workspace.id})
        return workspace

    async def create(
            self,
            workspace_data: WorkspaceCreateDTO,
            current_user: UUID,
            record_change: bool = False,
    ) -> WorkspaceDTO:
        workspace = await self._create_core(workspace_data, current_user, deferred=False)
        assert workspace is not None
        if record_change:
            await self._add_workspace_change(
                workspace.id,
                workspace.version,
                [
                    UnionOperation(
                        root=WorkspaceCreateOperation(
                            data=WorkspaceCreateDTO(
                                id=workspace.id,
                                name=workspace.name,
                                description=workspace.description,
                                owner_id=workspace.owner_id,
                            ),
                        )
                    )
                ],
            )
        return workspace

    async def create_deferred(
            self,
            workspace_data: WorkspaceCreateDTO,
            current_user: UUID,
    ) -> None:
        await self._create_core(workspace_data, current_user, deferred=True)

    @staticmethod
    def _same_workspaces(first_workspace: WorkspaceDTO, second_workspace: WorkspaceCreateDTO) -> bool:
        return all(
            getattr(first_workspace, field) == value
            for field, value in second_workspace
        )

    async def patch(
            self,
            patch_data: WorkspacePatchDTO,
            current_user: UUID,
            *,
            expected_workspace_version: int | None = None,
            record_change: bool = False,
    ) -> WorkspaceDTO:
        await self._ensure_editor_access(current_user, patch_data.id)

        patch_fields = patch_data.model_dump(exclude_unset=True)
        patch_fields.pop('id', None)
        patch_fields.pop('owner_id', None)

        current_workspace = await self.uow.workspaces.get(patch_data.id)
        if current_workspace is None:
            self._log_warning("Workspace not found", extra={'workspace_id': patch_data.id})
            raise EntityNotFound(WorkspaceDTO)

        if not patch_fields:
            return current_workspace

        new_version: int | None = None
        if expected_workspace_version is not None:
            new_version = await self._bump_workspace_version_or_raise(
                patch_data.id,
                expected_workspace_version,
            )

        updated: WorkspaceDTO | None = await self.uow.workspaces.update(patch_data.id, **patch_fields)
        if not updated:
            self._log_warning("Workspace not found", extra={'workspace_id': patch_data.id})
            raise EntityNotFound(WorkspaceDTO)

        if record_change and new_version is not None:
            await self._add_workspace_change(
                patch_data.id,
                new_version,
                [
                    UnionOperation(
                        root=WorkspacePatchOperation(
                            data=WorkspacePatchDTO(id=patch_data.id, **patch_fields),
                        )
                    )
                ],
            )
        self._log_info("Workspace was updated", extra={'workspace_id': updated.id})
        return updated

    async def delete(
            self,
            workspace_id: UUID,
            current_user: UUID,
            *,
            expected_workspace_version: int | None = None,
            record_change: bool = False,
    ) -> None:
        await self._ensure_editor_access(current_user, workspace_id)

        new_version: int | None = None
        if expected_workspace_version is not None:
            new_version = await self._bump_workspace_version_or_raise(
                workspace_id,
                expected_workspace_version,
            )

        deleted = await self.uow.workspaces.delete(workspace_id)
        if not deleted:
            self._log_warning("Workspace not found", extra={'workspace_id': workspace_id})
            raise EntityNotFound(WorkspaceDTO)

        if record_change and new_version is not None:
            await self._add_workspace_change(
                workspace_id,
                new_version,
                [
                    UnionOperation(
                        root=WorkspaceDeleteOperation(id=workspace_id)
                    )
                ],
            )
        self._log_info("Workspace was deleted", extra={'workspace_id': workspace_id})

    async def list_for_user(self, current_user: UUID) -> list[WorkspaceDTO]:
        return await self.uow.workspaces.get_accessible_user_workspaces(current_user)

    async def list_with_lists_for_user(self, current_user: UUID) -> list[WorkspaceRelListDTO]:
        return await self.uow.workspaces.get_accessible_user_workspaces_with_lists(current_user)

    async def get_with_lists(
            self,
            workspace_id: UUID,
            current_user: UUID,
    ) -> WorkspaceRelListDTO:
        await self._ensure_member_access(current_user, workspace_id)
        workspace = await self.uow.workspaces.get_workspace_with_lists(workspace_id)
        if not workspace:
            self._log_warning("Workspace not found", extra={'workspace_id': workspace_id})
            raise EntityNotFound(WorkspaceDTO)
        return workspace
