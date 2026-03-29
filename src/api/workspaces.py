import uuid

from fastapi import APIRouter, status

from api.docs.responses import (
    AUTH_REQUIRED_RESPONSE,
    NOT_FOUND_RESPONSE,
    SYNC_PAYLOAD_RESPONSE,
    UUID_CONFLICT_RESPONSE,
    VERSION_CONFLICT_RESPONSE,
)
from api.dependencies import CurrentUser, UoWDep
from api.schemas.workspace_invites import CreateInviteRequestDTO, JoinByInviteRequestDTO
from api.schemas.workspace_members import UpdateMemberRoleRequestDTO
from api.schemas.workspaces import (
    WorkspaceCreateRequestDTO,
    WorkspaceDeleteRequestDTO,
    WorkspacePatchRequestDTO,
)
from schemas.workspace_changes import (
    WorkspaceChangeCreateDTO,
    WorkspaceVersionDTO,
    WorkspacePushResultDTO,
)
from schemas.workspace_invites import InviteCodeResponseDTO
from schemas.workspace_members import WorkspaceMemberDTO
from schemas.workspaces import WorkspaceCreateDTO, WorkspacePatchDTO, WorkspaceDTO, WorkspaceRelListDTO
from services.workspace_invites import WorkspaceInviteService
from services.workspace_members import WorkspaceMembersService
from services.workspace_sync import WorkspaceSyncService
from services.workspaces import WorkspacesService

router = APIRouter(prefix='/workspaces', tags=['workspaces'])


@router.get(
    '',
    response_model=list[WorkspaceDTO],
    summary='List accessible workspaces',
    description='Returns all workspaces available to the current user.',
    responses=AUTH_REQUIRED_RESPONSE,
)
async def list_workspaces(
        current_user: CurrentUser,
        uow: UoWDep,
) -> list[WorkspaceDTO]:
    workspaces_service = WorkspacesService(uow)
    return await workspaces_service.list_for_user(current_user.id)


@router.get(
    '/full',
    response_model=list[WorkspaceRelListDTO],
    summary='List workspaces with shopping lists',
    description='Returns accessible workspaces together with nested shopping lists and items.',
    responses=AUTH_REQUIRED_RESPONSE,
)
async def list_workspaces_with_lists(
        current_user: CurrentUser,
        uow: UoWDep,
) -> list[WorkspaceRelListDTO]:
    workspaces_service = WorkspacesService(uow)
    return await workspaces_service.list_with_lists_for_user(current_user.id)


@router.get(
    '/{workspace_id}',
    response_model=WorkspaceRelListDTO,
    summary='Get workspace details',
    description='Returns a single workspace with its shopping lists and list items.',
    responses={
        **AUTH_REQUIRED_RESPONSE,
        **NOT_FOUND_RESPONSE,
    },
)
async def get_workspace(
        workspace_id: uuid.UUID,
        current_user: CurrentUser,
        uow: UoWDep,
) -> WorkspaceRelListDTO:
    workspaces_service = WorkspacesService(uow)
    return await workspaces_service.get_with_lists(workspace_id, current_user.id)


@router.post(
    '',
    response_model=WorkspaceDTO,
    status_code=status.HTTP_201_CREATED,
    summary='Create workspace',
    description='Creates a new workspace for the current user and records the change for sync.',
    responses={
        **AUTH_REQUIRED_RESPONSE,
        **UUID_CONFLICT_RESPONSE,
    },
)
async def create_workspace(
        payload: WorkspaceCreateRequestDTO,
        current_user: CurrentUser,
        uow: UoWDep,
) -> WorkspaceDTO:
    workspaces_service = WorkspacesService(uow)
    workspace_data = WorkspaceCreateDTO(
        id=payload.id,
        name=payload.name,
        description=payload.description,
    )
    workspace = await workspaces_service.create(
        workspace_data,
        current_user.id,
        record_change=True,
    )
    await uow.commit()
    return workspace


@router.patch(
    '/{workspace_id}',
    response_model=WorkspaceDTO,
    summary='Update workspace',
    description='Updates workspace fields.',
    responses={
        **AUTH_REQUIRED_RESPONSE,
        **NOT_FOUND_RESPONSE,
        **VERSION_CONFLICT_RESPONSE,
    },
)
async def patch_workspace(
        workspace_id: uuid.UUID,
        payload: WorkspacePatchRequestDTO,
        current_user: CurrentUser,
        uow: UoWDep,
) -> WorkspaceDTO:
    workspaces_service = WorkspacesService(uow)
    patch_fields = payload.model_dump(exclude={'workspace_version'}, exclude_unset=True)
    patch_data = WorkspacePatchDTO(id=workspace_id, **patch_fields)
    workspace = await workspaces_service.patch(
        patch_data,
        current_user.id,
        expected_workspace_version=payload.workspace_version,
        record_change=True,
    )
    await uow.commit()
    return workspace


@router.delete(
    '/{workspace_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Delete workspace',
    description='Soft-deletes a workspace.',
    responses={
        **AUTH_REQUIRED_RESPONSE,
        **NOT_FOUND_RESPONSE,
        **VERSION_CONFLICT_RESPONSE,
    },
)
async def delete_workspace(
        workspace_id: uuid.UUID,
        payload: WorkspaceDeleteRequestDTO,
        current_user: CurrentUser,
        uow: UoWDep,
) -> None:
    workspaces_service = WorkspacesService(uow)
    await workspaces_service.delete(
        workspace_id,
        current_user.id,
        expected_workspace_version=payload.workspace_version,
        record_change=True,
    )
    await uow.commit()


@router.post(
    '/sync/pull',
    response_model=list[WorkspaceChangeCreateDTO],
    status_code=status.HTTP_200_OK,
    summary='Pull workspace changes',
    description='Returns workspace changes newer than the versions known by the client.',
    responses={
        **AUTH_REQUIRED_RESPONSE,
        **NOT_FOUND_RESPONSE,
        **SYNC_PAYLOAD_RESPONSE,
    },
)
async def pull_workspace_changes(
        versions: list[WorkspaceVersionDTO],
        current_user: CurrentUser,
        uow: UoWDep,
) -> list[WorkspaceChangeCreateDTO]:
    sync_service = WorkspaceSyncService(uow)
    changes = await sync_service.pull_changes(current_user.id, versions)
    return changes


@router.post(
    '/sync/push',
    response_model=list[WorkspacePushResultDTO],
    status_code=status.HTTP_200_OK,
    summary='Push workspace changes',
    description='Applies a client sync payload and returns per-workspace push results.',
    responses={
        **AUTH_REQUIRED_RESPONSE,
        **NOT_FOUND_RESPONSE,
        **SYNC_PAYLOAD_RESPONSE,
    },
)
async def push_workspace_changes(
        changes: list[WorkspaceChangeCreateDTO],
        current_user: CurrentUser,
        uow: UoWDep,
) -> list[WorkspacePushResultDTO]:
    sync_service = WorkspaceSyncService(uow)
    result = await sync_service.push_changes(current_user.id, changes)
    await uow.commit()
    return result


@router.post(
    '/{workspace_id}/invites',
    response_model=InviteCodeResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary='Create invite code',
    description='Generates a join code for a workspace with the requested role and invite limits.',
    responses={
        **AUTH_REQUIRED_RESPONSE,
        **NOT_FOUND_RESPONSE,
    },
)
async def create_workspace_invite(
        workspace_id: uuid.UUID,
        payload: CreateInviteRequestDTO,
        current_user: CurrentUser,
        uow: UoWDep,
) -> InviteCodeResponseDTO:
    invite_service = WorkspaceInviteService(uow)
    return await invite_service.create_invite(
        workspace_id,
        current_user.id,
        payload.role,
        payload.max_uses,
        payload.expires_in_hours,
    )


@router.post(
    '/join-by-invite',
    response_model=WorkspaceDTO,
    status_code=status.HTTP_200_OK,
    summary='Join workspace by invite code',
    description='Adds the current user to a workspace using an active invite code.',
    responses={
        **AUTH_REQUIRED_RESPONSE,
        **NOT_FOUND_RESPONSE,
    },
)
async def join_workspace_by_invite(
        payload: JoinByInviteRequestDTO,
        current_user: CurrentUser,
        uow: UoWDep,
) -> WorkspaceDTO:
    invite_service = WorkspaceInviteService(uow)
    return await invite_service.join_workspace(payload.code, current_user.id)


@router.get(
    '/{workspace_id}/members',
    response_model=list[WorkspaceMemberDTO],
    summary='List workspace members',
    description='Returns all members of the workspace visible to the current user.',
    responses={
        **AUTH_REQUIRED_RESPONSE,
        **NOT_FOUND_RESPONSE,
    },
)
async def list_workspace_members(
        workspace_id: uuid.UUID,
        current_user: CurrentUser,
        uow: UoWDep,
) -> list[WorkspaceMemberDTO]:
    members_service = WorkspaceMembersService(uow)
    return await members_service.get_members(workspace_id, current_user.id)


@router.patch(
    '/{workspace_id}/members/{user_id}',
    response_model=WorkspaceMemberDTO,
    summary='Update member role',
    description='Changes the role of a workspace member. Restricted to the workspace owner.',
    responses={
        **AUTH_REQUIRED_RESPONSE,
        **NOT_FOUND_RESPONSE,
    },
)
async def update_member_role(
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
        payload: UpdateMemberRoleRequestDTO,
        current_user: CurrentUser,
        uow: UoWDep,
) -> WorkspaceMemberDTO:
    members_service = WorkspaceMembersService(uow)
    return await members_service.update_member_role(
        workspace_id,
        user_id,
        current_user.id,
        payload.role,
    )


@router.delete(
    '/{workspace_id}/members/{user_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Remove workspace member',
    description='Removes a user from the workspace. Restricted to the workspace owner.',
    responses={
        **AUTH_REQUIRED_RESPONSE,
        **NOT_FOUND_RESPONSE,
    },
)
async def remove_member(
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
        current_user: CurrentUser,
        uow: UoWDep,
) -> None:
    members_service = WorkspaceMembersService(uow)
    await members_service.remove_member(workspace_id, user_id, current_user.id)
