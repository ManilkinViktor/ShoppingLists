from uuid import UUID

from schemas.workspaces import WorkspaceAddDTO, WorkspaceDTO
from database.models.workspace_members import Role
from services.base import BaseService
from services.exceptions import ConflictUUID


class WorkspacesService(BaseService):

    async def create(self, current_user: UUID, workspace_data: WorkspaceAddDTO) -> WorkspaceDTO:
        found_workspace: WorkspaceDTO = await self.uow.workspaces.get(workspace_data.id)
        if found_workspace:
            if self._same_workspaces(found_workspace, workspace_data):
                self._log_info("Workspace already exists", extra={'workspace_id': found_workspace.id})
                workspace: WorkspaceDTO = found_workspace
            else:
                self._log_warning("Conflict uuid: workspace with same uuid and another data exists")
                raise ConflictUUID
        else:
            workspace_data.owner_id = current_user
            workspace: WorkspaceDTO = await self.uow.workspaces.add(workspace_data)
            await self.uow.workspace_members.add(workspace_id=workspace.id, user_id=current_user, role=Role.editor)
            self._log_info("Workspace was created", extra={'workspace_id': workspace.id})
        return workspace

    @staticmethod
    def _same_workspaces(first_workspace: WorkspaceDTO, second_workspace: WorkspaceAddDTO) -> bool:
        return all(
            getattr(first_workspace, field) == value
            for field, value in second_workspace
        )

