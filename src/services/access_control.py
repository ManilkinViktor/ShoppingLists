from uuid import UUID
from logging import WARNING

from core.enums import Role
from schemas.workspaces import WorkspaceDTO
from schemas.workspace_members import WorkspaceMemberDTO
from services.exceptions import EntityNotFound

class AccessController:
    def __init__(self, uow, logger):
        self.uow = uow
        self.logger = logger


    async def ensure_member_access(
        self,
        current_user: UUID,
        workspace_id: UUID,
        entity_type: type = WorkspaceDTO,
    ):
        member = await self.uow.workspace_members.get_by(
            user_id=current_user,
            workspace_id=workspace_id,
        )
        if not member:
            self.uow.log(self.logger, WARNING, "User doesn't have access to entity",
                         extra={'workspace_id': workspace_id, 'user_id': current_user}, immediate=True)
            raise EntityNotFound(entity_type)

    async def ensure_editor_access(
        self,
        current_user: UUID,
        workspace_id: UUID,
        editable_workspace_ids: set[UUID] | None = None,
        entity_type: type = WorkspaceDTO,
    ):
        if editable_workspace_ids is not None:
            if workspace_id in editable_workspace_ids:
                return
            self.uow.log(self.logger, WARNING, "User doesn't have access to entity (editor)",
                         extra={'workspace_id': workspace_id, 'user_id': current_user}, immediate=True)
            raise EntityNotFound(entity_type)
        member = await self.uow.workspace_members.get_by(
            user_id=current_user,
            workspace_id=workspace_id,
        )
        if not member or member.role != Role.editor:
            self.uow.log(self.logger, WARNING, "User doesn't have access to entity (editor)",
                         extra={'workspace_id': workspace_id, 'user_id': current_user}, immediate=True)
            raise EntityNotFound(entity_type)

    async def ensure_owner_access(self, current_user: UUID, workspace_id: UUID, entity_type: type = WorkspaceDTO):
        workspace = await self.uow.workspaces.get(workspace_id)
        if not workspace or workspace.owner_id != current_user:
            self.uow.log(self.logger, WARNING, "User is not the owner of workspace",
                         extra={'workspace_id': workspace_id, 'user_id': current_user}, immediate=True)
            raise EntityNotFound(entity_type)
        return workspace

    async def check_member_exists(self, workspace_id: UUID, user_id: UUID):
        member = await self.uow.workspace_members.get_by(
            workspace_id=workspace_id,
            user_id=user_id,
        )
        if not member:
            self.uow.log(self.logger, WARNING, "Member not found", extra={'workspace_id': workspace_id, 'user_id': user_id}, immediate=True)
            raise EntityNotFound(WorkspaceMemberDTO)
        return member
