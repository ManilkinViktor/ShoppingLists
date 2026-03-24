from logging import Logger, DEBUG, INFO, WARNING, ERROR, CRITICAL
from uuid import UUID

from core.logger import LoggerMeta
from database.uow import UnitOfWork
from schemas.workspace_changes import WorkspaceChangeCreateDTO, UnionOperation
from schemas.workspaces import WorkspaceDTO
from services.exceptions import EntityNotFound, WorkspaceVersionMismatch


class BaseService(metaclass=LoggerMeta):
    logger: Logger

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow: UnitOfWork = uow

    # methods for logging after commit

    def _log_debug(self, msg: str, *args, immediate: bool = False, **kwargs) -> None:
        self.uow.log(self.logger, DEBUG, msg, *args, immediate=immediate, **kwargs)

    def _log_info(self, msg: str, *args, immediate: bool = False, **kwargs) -> None:
        self.uow.log(self.logger, INFO, msg, *args, immediate=immediate, **kwargs)

    def _log_warning(self, msg: str, *args, immediate: bool = False, **kwargs) -> None:
        self.uow.log(self.logger, WARNING, msg, *args, immediate=immediate, **kwargs)

    def _log_error(self, msg: str, *args, **kwargs) -> None:
        # Для error и выше всегда immediate
        self.uow.log(self.logger, ERROR, msg, *args, immediate=True, **kwargs)

    def _log_critical(self, msg: str, *args, **kwargs) -> None:
        self.uow.log(self.logger, CRITICAL, msg, *args, immediate=True, **kwargs)

    async def _bump_workspace_version_or_raise(
            self,
            workspace_id: UUID,
            workspace_version: int,
    ) -> int:
        bumped = await self.uow.workspaces.compare_and_bump_version(workspace_id, workspace_version)
        if bumped:
            return workspace_version + 1

        workspace = await self.uow.workspaces.get(workspace_id)
        if workspace is None:
            raise EntityNotFound(WorkspaceDTO)

        self._log_warning(
            'Workspace version mismatch',
            extra={'workspace_id': workspace_id, 'workspace_version': workspace_version},
            immediate=True,
        )
        raise WorkspaceVersionMismatch

    async def _add_workspace_change(
            self,
            workspace_id: UUID,
            workspace_version: int,
            changes: list[UnionOperation],
    ) -> None:
        await self.uow.workspace_changes.add_all(
            [
                WorkspaceChangeCreateDTO(
                    workspace_id=workspace_id,
                    workspace_version=workspace_version,
                    changes=changes,
                )
            ]
        )
