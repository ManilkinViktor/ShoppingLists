from collections.abc import AsyncIterator
from logging import Logger
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories.workspaces import WorkspacesRepository
from database.repositories.workspace_members import WorkspaceMembersRepository
from database.repositories.list_items import ListItemsRepository
from database.repositories.shopping_lists import ShoppingListsRepository
from database.repositories.workspace_changes import WorkspaceChangesRepository
from database.repositories.users import UsersRepository
from database.repositories.refresh_sessions import RefreshSessionsRepository

from database.session import session_factory

class UnitOfWork:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._users: UsersRepository | None = None
        self._workspaces: WorkspacesRepository | None = None
        self._workspace_members: WorkspaceMembersRepository | None = None
        self._shopping_lists: ShoppingListsRepository | None = None
        self._list_items: ListItemsRepository | None = None
        self._workspace_changes: WorkspaceChangesRepository | None = None
        self._refresh_sessions: RefreshSessionsRepository | None = None
        self._aggregator_logs: list[tuple[Logger, dict[str, Any]]] = []

    async def __aenter__(self) -> "UnitOfWork":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type:
           await self._session.rollback()
        await self._session.close()

    async def commit(self) -> None:
        try:
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise
        await self._flush_logs()

    def set_defer_flush(self, enabled: bool) -> None:
        if enabled:
            self._session.info['defer_flush'] = True
        else:
            self._session.info.pop('defer_flush', None)

    def log(self, logger_obj: Logger, level: int, msg: str, *args, **kwargs) -> None:
        self._aggregator_logs.append((logger_obj, {
            'level': level,
            'msg': msg,
            'args': args,
            'kwargs': kwargs,
        }))

    async def _flush_logs(self) -> None:
        for logger_obj, entry in self._aggregator_logs:
            logger_obj.log(
                entry['level'],
                entry['msg'],
                *entry['args'],
                **entry['kwargs']
            )


    @property
    def users(self) -> UsersRepository:
        if self._users is None:
            self._users = UsersRepository(self._session)
        return self._users

    @property
    def workspaces(self) -> WorkspacesRepository:
        if self._workspaces is None:
            self._workspaces = WorkspacesRepository(self._session)
        return self._workspaces

    @property
    def workspace_members(self) -> WorkspaceMembersRepository:
        if self._workspace_members is None:
            self._workspace_members = WorkspaceMembersRepository(self._session)
        return self._workspace_members

    @property
    def shopping_lists(self) -> ShoppingListsRepository:
        if self._shopping_lists is None:
            self._shopping_lists = ShoppingListsRepository(self._session)
        return self._shopping_lists

    @property
    def list_items(self) -> ListItemsRepository:
        if self._list_items is None:
            self._list_items = ListItemsRepository(self._session)
        return self._list_items

    @property
    def workspace_changes(self) -> WorkspaceChangesRepository:
        if self._workspace_changes is None:
            self._workspace_changes = WorkspaceChangesRepository(self._session)
        return self._workspace_changes

    @property
    def refresh_sessions(self) -> RefreshSessionsRepository:
        if self._refresh_sessions is None:
            self._refresh_sessions = RefreshSessionsRepository(self._session)
        return self._refresh_sessions

    @classmethod
    async def get_with(cls) -> AsyncIterator["UnitOfWork"]:
        """
        using:
        uow: UnitOfWork = Depends(UnitOfWork.get_with)
        """
        async with session_factory() as session:
            async with cls(session) as uow:
                yield uow
