from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories.workspaces import WorkspacesRepository
from database.repositories.workspace_members import WorkspaceMembersRepository
from database.repositories.list_items import ListItemsRepository
from database.repositories.shopping_lists import ShoppingListsRepository
from database.repositories.users import UsersRepository

from database.session import session_factory

class UnitOfWork:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._users: UsersRepository | None = None
        self._workspaces: WorkspacesRepository | None = None
        self._workspace_members: WorkspaceMembersRepository | None = None
        self._shopping_lists: ShoppingListsRepository | None = None
        self._list_items: ListItemsRepository | None = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
           await self._session.rollback()
        else:
            await self._session.commit()
        await self._session.close()


    @property
    def users(self):
        if self._users is None:
            self._users = UsersRepository(self._session)
        return self._users

    @property
    def workspaces(self):
        if self._workspaces is None:
            self._workspaces = WorkspacesRepository(self._session)
        return self._workspaces

    @property
    def workspace_members(self):
        if self._workspace_members is None:
            self._workspace_members = WorkspaceMembersRepository(self._session)
        return self._workspace_members

    @property
    def shopping_lists(self):
        if self._shopping_lists is None:
            self._shopping_lists = ShoppingListsRepository(self._session)
        return self._session

    @property
    def list_items(self):
        if self._list_items is None:
            self._list_items = ListItemsRepository(self._session)
        return self._list_items

    @classmethod
    async def get_with(cls):
        """
        used for Depends
        :return:
        """
        async with session_factory() as session:
            yield cls(session)