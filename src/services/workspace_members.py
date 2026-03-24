from uuid import UUID

from core.enums import Role
from database.uow import UnitOfWork
from schemas.workspace_members import WorkspaceMemberDTO
from schemas.workspaces import WorkspaceDTO
from services.base import BaseService
from services.exceptions import EntityNotFound, DomainException


class WorkspaceMembersService(BaseService):

    async def _ensure_owner_access(self, current_user: UUID, workspace_id: UUID) -> None:
        workspace = await self.uow.workspaces.get(workspace_id)
        if not workspace or workspace.owner_id != current_user:
            self._log_warning(
                "User is not the owner of workspace",
                extra={'workspace_id': workspace_id, 'user_id': current_user},
            )
            raise EntityNotFound(WorkspaceDTO)

    async def _check_member_exists(self, workspace_id: UUID, user_id: UUID) -> WorkspaceMemberDTO:
        member = await self.uow.workspace_members.get_by(
            workspace_id=workspace_id,
            user_id=user_id,
        )
        if not member:
            self._log_warning(
                "Member not found",
                extra={'workspace_id': workspace_id, 'user_id': user_id},
            )
            raise EntityNotFound(WorkspaceMemberDTO)
        return member

    async def update_member_role(
        self,
        workspace_id: UUID,
        user_id: UUID,
        current_user: UUID,
        new_role: Role,
    ) -> WorkspaceMemberDTO:
        await self._ensure_owner_access(current_user, workspace_id)
        member = await self._check_member_exists(workspace_id, user_id)

        old_role = member.role
        member.role = new_role
        await self.uow.commit()

        self._log_info(
            "Member role updated",
            extra={
                'workspace_id': workspace_id,
                'user_id': user_id,
                'old_role': old_role,
                'new_role': new_role,
            }
        )

        return member

    async def remove_member(
        self,
        workspace_id: UUID,
        user_id: UUID,
        current_user: UUID,
    ) -> None:
        await self._ensure_owner_access(current_user, workspace_id)
        await self._check_member_exists(workspace_id, user_id)

        await self.uow.workspace_members.delete_by(
            workspace_id=workspace_id,
            user_id=user_id,
        )
        await self.uow.commit()

        self._log_info(
            "Member removed from workspace",
            extra={'workspace_id': workspace_id, 'user_id': user_id}
        )

    async def get_members(
        self,
        workspace_id: UUID,
        current_user: UUID,
    ) -> list[WorkspaceMemberDTO]:
        member = await self.uow.workspace_members.get_by(
            workspace_id=workspace_id,
            user_id=current_user,
        )
        if not member:
            self._log_warning(
                "User is not a member of workspace",
                extra={'workspace_id': workspace_id, 'user_id': current_user},
            )
            raise EntityNotFound(WorkspaceDTO)

        return await self.uow.workspace_members.get_all(workspace_id=workspace_id)