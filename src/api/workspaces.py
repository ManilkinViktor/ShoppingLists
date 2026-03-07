from fastapi import APIRouter, status
from sqlalchemy.exc import IntegrityError

from api.dependencies import CurrentUser, UoWDep
from api.http_exceptions import domain_to_http_exception, integrity_error_to_http_exception
from schemas.workspace_changes import WorkspaceChangeCreateDTO, WorkspaceSyncResultDTO
from services.exceptions import DomainException
from services.workspaces import WorkspacesService


router = APIRouter(prefix='/workspaces', tags=['workspaces'])


@router.post('/sync', response_model=list[WorkspaceSyncResultDTO], status_code=status.HTTP_200_OK)
async def sync_workspaces(
    changes: list[WorkspaceChangeCreateDTO],
    current_user: CurrentUser,
    uow: UoWDep,
) -> list[WorkspaceSyncResultDTO]:
    workspaces_service = WorkspacesService(uow)
    try:
        sync_result = await workspaces_service.sync(current_user.id, changes)
        await uow.commit()
    except DomainException as error:
        raise domain_to_http_exception(error)
    except IntegrityError as error:
        raise integrity_error_to_http_exception(error)
    return sync_result
