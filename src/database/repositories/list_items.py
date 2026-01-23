from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories.base import BaseRepository
from database.models import ListItemsOrm
from schemas.list_items import ListItemDTO


class ShoppingListsRepository(
    BaseRepository[
        ListItemsOrm,
        ListItemDTO,
        ListItemDTO
    ]):

        def __init__(self, _session: AsyncSession):
            super().__init__(
                _session,
                _model=ListItemsOrm, _add_dto=ListItemDTO, _dto=ListItemDTO
            )