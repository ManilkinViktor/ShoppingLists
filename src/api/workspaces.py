import uuid

from fastapi import APIRouter, status
from sqlalchemy.exc import IntegrityError

from api.dependencies import CurrentUser, UoWDep
from api.http_exceptions import domain_to_http_exception, integrity_error_to_http_exception
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
from schemas.workspaces import WorkspaceCreateDTO, WorkspacePatchDTO, WorkspaceDTO, WorkspaceRelListDTO
from services.exceptions import DomainException
from services.workspace_sync import WorkspaceSyncService
from services.workspaces import WorkspacesService

router = APIRouter(prefix='/workspaces', tags=['workspaces'])


@router.get('', response_model=list[WorkspaceDTO])
async def list_workspaces(
        current_user: CurrentUser,
        uow: UoWDep,
) -> list[WorkspaceDTO]:
    workspaces_service = WorkspacesService(uow)
    try:
        return await workspaces_service.list_for_user(current_user.id)
    except DomainException as error:
        raise domain_to_http_exception(error) from None
    except IntegrityError as error:
        raise integrity_error_to_http_exception(error) from None


@router.get('/full', response_model=list[WorkspaceRelListDTO])
async def list_workspaces_with_lists(
        current_user: CurrentUser,
        uow: UoWDep,
) -> list[WorkspaceRelListDTO]:
    workspaces_service = WorkspacesService(uow)
    try:
        return await workspaces_service.list_with_lists_for_user(current_user.id)
    except DomainException as error:
        raise domain_to_http_exception(error) from None
    except IntegrityError as error:
        raise integrity_error_to_http_exception(error) from None


@router.get('/{workspace_id}', response_model=WorkspaceRelListDTO)
async def get_workspace(
        workspace_id: uuid.UUID,
        current_user: CurrentUser,
        uow: UoWDep,
) -> WorkspaceRelListDTO:
    workspaces_service = WorkspacesService(uow)
    try:
        return await workspaces_service.get_with_lists(workspace_id, current_user.id)
    except DomainException as error:
        raise domain_to_http_exception(error) from None
    except IntegrityError as error:
        raise integrity_error_to_http_exception(error) from None


@router.post('', response_model=WorkspaceDTO, status_code=status.HTTP_201_CREATED)
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
    try:
        workspace = await workspaces_service.create(
            workspace_data,
            current_user.id,
            record_change=True,
        )
        await uow.commit()
    except DomainException as error:
        raise domain_to_http_exception(error) from None
    except IntegrityError as error:
        raise integrity_error_to_http_exception(error) from None
    return workspace


@router.patch('/{workspace_id}', response_model=WorkspaceDTO)
async def patch_workspace(
        workspace_id: uuid.UUID,
        payload: WorkspacePatchRequestDTO,
        current_user: CurrentUser,
        uow: UoWDep,
) -> WorkspaceDTO:
    workspaces_service = WorkspacesService(uow)
    try:
        patch_fields = payload.model_dump(exclude={'workspace_version'}, exclude_unset=True)
        patch_data = WorkspacePatchDTO(id=workspace_id, **patch_fields)
        workspace = await workspaces_service.patch(
            patch_data,
            current_user.id,
            expected_workspace_version=payload.workspace_version,
            record_change=True,
        )
        await uow.commit()
    except DomainException as error:
        raise domain_to_http_exception(error) from None
    except IntegrityError as error:
        raise integrity_error_to_http_exception(error) from None
    return workspace


@router.delete('/{workspace_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
        workspace_id: uuid.UUID,
        payload: WorkspaceDeleteRequestDTO,
        current_user: CurrentUser,
        uow: UoWDep,
) -> None:
    workspaces_service = WorkspacesService(uow)
    try:
        await workspaces_service.delete(
            workspace_id,
            current_user.id,
            expected_workspace_version=payload.workspace_version,
            record_change=True,
        )
        await uow.commit()
    except DomainException as error:
        raise domain_to_http_exception(error) from None
    except IntegrityError as error:
        raise integrity_error_to_http_exception(error) from None


@router.post('/sync/pull', response_model=list[WorkspaceChangeCreateDTO], status_code=status.HTTP_200_OK)
async def pull_workspace_changes(
        versions: list[WorkspaceVersionDTO],
        current_user: CurrentUser,
        uow: UoWDep,
) -> list[WorkspaceChangeCreateDTO]:
    sync_service = WorkspaceSyncService(uow)
    try:
        changes = await sync_service.pull_changes(current_user.id, versions)
    except DomainException as error:
        raise domain_to_http_exception(error) from None
    except IntegrityError as error:
        raise integrity_error_to_http_exception(error) from None
    return changes


@router.post('/sync/push', response_model=list[WorkspacePushResultDTO], status_code=status.HTTP_200_OK)
async def push_workspace_changes(
        changes: list[WorkspaceChangeCreateDTO],
        current_user: CurrentUser,
        uow: UoWDep,
) -> list[WorkspacePushResultDTO]:
    sync_service = WorkspaceSyncService(uow)
    try:
        result = await sync_service.push_changes(current_user.id, changes)
        await uow.commit()
    except DomainException as error:
        raise domain_to_http_exception(error) from None
    except IntegrityError as error:
        raise integrity_error_to_http_exception(error) from None
    return result
