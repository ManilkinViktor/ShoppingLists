import datetime
import secrets
import string
from uuid import UUID

from core.enums import Role
from database.models import WorkspaceInvitesOrm
from database.uow import UnitOfWork
from schemas.workspace_invites import WorkspaceInviteCreateDTO, WorkspaceInviteDTO, InviteCodeResponseDTO
from schemas.workspace_members import WorkspaceMemberCreateDTO
from schemas.workspaces import WorkspaceDTO
from services.base import BaseService
from services.exceptions import EntityNotFound, DomainException
from services.access_control import AccessController
from utils.datetime_utils import utc_now


class WorkspaceInviteService(BaseService):
    INVITE_CODE_LENGTH = 24

    def __init__(self, uow: UnitOfWork) -> None:
        super().__init__(uow)
        self._access_control = AccessController(uow, self.logger)

    @staticmethod
    def _generate_invite_code() -> str:
        chars = string.ascii_letters + string.digits
        return ''.join(secrets.choice(chars) for _ in range(WorkspaceInviteService.INVITE_CODE_LENGTH))


    async def create_invite(
        self,
        workspace_id: UUID,
        current_user: UUID,
        role: Role,
        max_uses: int | None = None,
        expires_in_hours: int = 24,
    ) -> InviteCodeResponseDTO:
        await self._access_control.ensure_owner_access(current_user, workspace_id, WorkspaceDTO)

        code = self._generate_invite_code()
        expires_at = utc_now() + datetime.timedelta(hours=expires_in_hours)

        invite = WorkspaceInvitesOrm(
            id=code,
            workspace_id=workspace_id,
            role=role,
            expires_at=expires_at,
            max_uses=max_uses,
        )
        self.uow._session.add(invite)
        await self.uow.commit()

        self._log_info(
            "Invitation code created",
            extra={'workspace_id': workspace_id, 'role': role, 'code': code}
        )

        return InviteCodeResponseDTO(
            code=code,
            role=role,
            expires_at=expires_at,
            max_uses=max_uses,
        )

    async def _validate_invite(self, invite: WorkspaceInviteDTO) -> None:

        if not invite.is_active:
            self._log_warning(
                "Invitation is inactive",
                extra={'code': invite.id, 'workspace_id': invite.workspace_id},
                immediate=True,
            )
            raise DomainException("Invitation is no longer active")

        now = utc_now()
        if now > invite.expires_at:
            self._log_warning(
                "Invitation has expired",
                extra={'code': invite.id, 'workspace_id': invite.workspace_id},
                immediate=True,
            )
            raise DomainException("Invitation has expired")

        if invite.max_uses and invite.current_uses >= invite.max_uses:
            self._log_warning(
                "Invitation max uses exceeded",
                extra={'code': invite.id, 'workspace_id': invite.workspace_id},
                immediate=True,
            )
            raise DomainException("Invitation has reached maximum uses")

    async def _check_user_not_member(self, current_user: UUID, workspace_id: UUID) -> None:
        existing_member = await self.uow.workspace_members.get_by(
            user_id=current_user,
            workspace_id=workspace_id,
        )
        if existing_member:
            self._log_info(
                "User is already a member of workspace",
                extra={'workspace_id': workspace_id, 'user_id': current_user},
                immediate=True,
            )
            raise DomainException("You are already a member of this workspace")

    async def _add_user_to_workspace(self, invite: WorkspaceInviteDTO, current_user: UUID) -> None:
        membership = WorkspaceMemberCreateDTO(
            workspace_id=invite.workspace_id,
            user_id=current_user,
            role=invite.role,
        )
        await self.uow.workspace_members.add(membership)

        invite.current_uses += 1
        if invite.max_uses and invite.current_uses >= invite.max_uses:
            invite.is_active = False

        self._log_info(
            "User joined workspace via invitation",
            extra={
                'workspace_id': invite.workspace_id,
                'user_id': current_user,
                'role': invite.role,
            }
        )

    async def join_workspace(self, code: str, current_user: UUID) -> WorkspaceDTO:
        invite = await self.uow.workspace_invites.get(code)
        if not invite:
            self._log_warning(
                "Invalid invitation code",
                extra={'code': code, 'user_id': current_user},
                immediate=True,
            )
            raise EntityNotFound(WorkspaceDTO)

        await self._validate_invite(invite)
        await self._check_user_not_member(current_user, invite.workspace_id)
        await self._add_user_to_workspace(invite, current_user)
        await self.uow.commit()

        workspace = await self.uow.workspaces.get(invite.workspace_id)
        assert workspace is not None
        return workspace

    async def list_invites(self, workspace_id: UUID, current_user: UUID) -> list[WorkspaceInviteDTO]:
        await self._access_control.ensure_owner_access(current_user, workspace_id, WorkspaceDTO)
        return await self.uow.workspace_invites.get_all(workspace_id=workspace_id)

    async def revoke_invite(self, code: str, current_user: UUID) -> None:
        invite = await self.uow.workspace_invites.get(code)
        if not invite:
            self._log_warning(
                "Invalid invitation code",
                extra={'code': code},
                immediate=True,
            )
            raise EntityNotFound(WorkspaceDTO)

        await self._access_control.ensure_owner_access(current_user, invite.workspace_id, WorkspaceDTO)

        invite.is_active = False
        await self.uow.commit()

        self._log_info(
            "Invitation code revoked",
            extra={'code': code, 'workspace_id': invite.workspace_id},
        )
