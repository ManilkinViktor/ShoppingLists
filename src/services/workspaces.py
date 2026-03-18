from uuid import UUID

from schemas.workspaces import WorkspaceCreateDTO, WorkspaceDTO, WorkspacePatchDTO, WorkspaceRelListDTO
from core.enums import Role
from database.uow import UnitOfWork
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

    async def create(self, workspace_data: WorkspaceCreateDTO, current_user: UUID) -> WorkspaceDTO:
        workspace_data = workspace_data.model_copy(update={'owner_id': current_user})
        found_workspace: WorkspaceDTO = await self.uow.workspaces.get(workspace_data.id)
        if found_workspace:
            if self._same_workspaces(found_workspace, workspace_data):
                self._log_info("Workspace already exists", extra={'workspace_id': found_workspace.id})
                workspace: WorkspaceDTO = found_workspace
            else:
                self._log_warning("Conflict uuid: workspace with same uuid and another data exists")
                raise ConflictUUID
        else:
            workspace: WorkspaceDTO = await self.uow.workspaces.add(workspace_data)
            await self.uow.workspace_members.add(workspace_id=workspace.id, user_id=current_user, role=Role.editor)
            self._log_info("Workspace was created", extra={'workspace_id': workspace.id})
        return workspace

    @staticmethod
    def _same_workspaces(first_workspace: WorkspaceDTO, second_workspace: WorkspaceCreateDTO) -> bool:
        return all(
            getattr(first_workspace, field) == value
            for field, value in second_workspace
        )

    async def patch(self, patch_data: WorkspacePatchDTO, current_user: UUID) -> WorkspaceDTO:
        await self._ensure_editor_access(current_user, patch_data.id)
        update_data = patch_data.model_dump(exclude_unset=True)
        update_data.pop('id', None)
        update_data.pop('owner_id', None)
        updated: WorkspaceDTO | None = await self.uow.workspaces.update(patch_data.id, **update_data)
        if not updated:
            self._log_warning("Workspace not found", extra={'workspace_id': patch_data.id})
            raise EntityNotFound(WorkspaceDTO)
        self._log_info("Workspace was updated", extra={'workspace_id': updated.id})
        return updated


    async def delete(self, workspace_id: UUID, current_user: UUID) -> None:
        await self._ensure_editor_access(current_user, workspace_id)
        deleted = await self.uow.workspaces.delete(workspace_id)
        if not deleted:
            self._log_warning("Workspace not found", extra={'workspace_id': workspace_id})
            raise EntityNotFound(WorkspaceDTO)
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
