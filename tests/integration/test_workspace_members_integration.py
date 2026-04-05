import sys
import uuid
from pathlib import Path

import pytest
from uuid_utils import uuid7

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.append(str(SRC_PATH))

from conftest import session_factory
from core.enums import Role
from database.uow import UnitOfWork
from schemas.users import UserCreateAuthDTO
from schemas.workspace_members import WorkspaceMemberCreateDTO
from schemas.workspaces import WorkspaceCreateDTO
from services.workspace_members import WorkspaceMembersService


@pytest.mark.asyncio
async def test_owner_can_update_workspace_member_role() -> None:
    owner_id = uuid.UUID(str(uuid7()))
    member_id = uuid.UUID(str(uuid7()))
    workspace_id = uuid.UUID(str(uuid7()))
    owner_email = f"workspace-owner-{workspace_id}@example.com"
    member_email = f"workspace-member-{workspace_id}@example.com"

    try:
        async with session_factory() as session:
            uow = UnitOfWork(session)
            await uow.users.add(
                UserCreateAuthDTO(
                    id=owner_id,
                    name="workspace-owner",
                    email=owner_email,
                    hashed_password="hashed",
                )
            )
            await uow.users.add(
                UserCreateAuthDTO(
                    id=member_id,
                    name="workspace-member",
                    email=member_email,
                    hashed_password="hashed",
                )
            )
            await uow.workspaces.add(
                WorkspaceCreateDTO(
                    id=workspace_id,
                    name="members-workspace",
                    description=None,
                    owner_id=owner_id,
                )
            )
            await uow.workspace_members.add(
                WorkspaceMemberCreateDTO(
                    workspace_id=workspace_id,
                    user_id=owner_id,
                    role=Role.editor,
                )
            )
            await uow.workspace_members.add(
                WorkspaceMemberCreateDTO(
                    workspace_id=workspace_id,
                    user_id=member_id,
                    role=Role.viewer,
                )
            )
            await uow.commit()

        async with session_factory() as session:
            uow = UnitOfWork(session)
            members_service = WorkspaceMembersService(uow)

            updated_member = await members_service.update_member_role(
                workspace_id=workspace_id,
                user_id=member_id,
                current_user=owner_id,
                new_role=Role.editor,
            )
            await uow.commit()

            assert updated_member.role == Role.editor

        async with session_factory() as session:
            uow = UnitOfWork(session)
            stored_member = await uow.workspace_members.get_by(
                workspace_id=workspace_id,
                user_id=member_id,
            )

            assert stored_member is not None
            assert stored_member.role == Role.editor

    finally:
        async with session_factory() as session:
            uow = UnitOfWork(session)
            await uow.workspace_members.delete_by(workspace_id, owner_id)
            await uow.workspace_members.delete_by(workspace_id, member_id)
            await uow.workspaces.delete(workspace_id)
            await uow.users.delete(owner_id)
            await uow.users.delete(member_id)
            await uow.commit()
