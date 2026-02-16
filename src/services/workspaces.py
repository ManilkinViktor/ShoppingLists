from schemas.workspaces import WorkspaceAddDTO, WorkspaceDTO
from services.base import BaseService
from services.exceptions import ConflictUUID


class WorkspacesService(BaseService):

    async def create(self, workspace_data: WorkspaceAddDTO) -> WorkspaceDTO:
        found_workspace: WorkspaceDTO = await self.uow.workspaces.get(workspace_data.id)
        if found_workspace:
            if self._same_workspaces(found_workspace, workspace_data):
                self._log_info("Workspace already exists", extra={'workspace_id': found_workspace.id})
                return found_workspace
            else:
                self._log_warning("Conflict uuid: workspace with same uuid and another data exists")
                raise ConflictUUID
        workspace: WorkspaceDTO = await self.uow.workspaces.add(workspace_data)
        self._log_info("Workspace was created", extra={'workspace_id': workspace.id})
        return workspace

    @staticmethod
    def _same_workspaces(first_workspace: WorkspaceAddDTO, second_workspace: WorkspaceAddDTO) -> bool:
        for field, value in first_workspace:
            if getattr(second_workspace, field) != value:
                return False
        return True


