import uuid

from fastapi import APIRouter, status
from sqlalchemy.exc import IntegrityError

from api.dependencies import CurrentUser, UoWDep
from api.http_exceptions import domain_to_http_exception, integrity_error_to_http_exception
from schemas.workspace_changes import WorkspaceChangeCreateDTO, WorkspaceSyncResultDTO
from schemas.workspaces import WorkspaceCreateDTO, WorkspacePatchDTO, WorkspaceDTO
from services.exceptions import DomainException
from services.workspaces import WorkspacesService
from services.workspace_sync import WorkspaceSyncService


router = APIRouter(prefix='/workspaces', tags=['workspaces'])


@router.post('', response_model=WorkspaceDTO, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    payload: WorkspaceCreateDTO,
    current_user: CurrentUser,
    uow: UoWDep,
) -> WorkspaceDTO:
    workspaces_service = WorkspacesService(uow)
    workspace_data = payload.model_copy(update={'owner_id': current_user.id})
    try:
        workspace = await workspaces_service.create(workspace_data, current_user.id)
        await uow.commit()
    except DomainException as error:
        raise domain_to_http_exception(error) from None
    except IntegrityError as error:
        raise integrity_error_to_http_exception(error) from None
    return workspace


@router.patch('/{workspace_id}', response_model=WorkspaceDTO)
async def patch_workspace(
    workspace_id: uuid.UUID,
    payload: WorkspacePatchDTO,
    current_user: CurrentUser,
    uow: UoWDep,
) -> WorkspaceDTO:
    workspaces_service = WorkspacesService(uow)
    update_data = payload.model_dump(exclude_unset=True)
    update_data.pop('id', None)
    update_data.pop('owner_id', None)
    patch_data = WorkspacePatchDTO(id=workspace_id, **update_data)
    try:
        workspace = await workspaces_service.patch(patch_data, current_user.id)
        await uow.commit()
    except DomainException as error:
        raise domain_to_http_exception(error) from None
    except IntegrityError as error:
        raise integrity_error_to_http_exception(error) from None
    return workspace


@router.delete('/{workspace_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: uuid.UUID,
    current_user: CurrentUser,
    uow: UoWDep,
) -> None:
    workspaces_service = WorkspacesService(uow)
    try:
        await workspaces_service.delete(workspace_id, current_user.id)
        await uow.commit()
    except DomainException as error:
        raise domain_to_http_exception(error) from None
    except IntegrityError as error:
        raise integrity_error_to_http_exception(error) from None


@router.post('/sync', response_model=list[WorkspaceSyncResultDTO], status_code=status.HTTP_200_OK)
async def sync_workspaces(
    changes: list[WorkspaceChangeCreateDTO],
    current_user: CurrentUser,
    uow: UoWDep,
) -> list[WorkspaceSyncResultDTO]:
    sync_service = WorkspaceSyncService(uow)
    try:
        sync_result = await sync_service.sync(current_user.id, changes)
        await uow.commit()
    except DomainException as error:
        raise domain_to_http_exception(error) from None
    except IntegrityError as error:
        raise integrity_error_to_http_exception(error) from None
    return sync_result


