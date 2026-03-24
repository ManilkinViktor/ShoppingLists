from sqlalchemy.ext.asyncio import AsyncSession

from database.models import ListItemsOrm
from database.repositories.base import BaseRepository
from schemas.list_items import ListItemDTO, ListItemCreateDTO


class ListItemsRepository(
    BaseRepository[
        ListItemsOrm,
        ListItemCreateDTO,
        ListItemDTO
    ]):

    def __init__(self, _session: AsyncSession) -> None:
        super().__init__(
            _session,
            _model=ListItemsOrm, _add_dto=ListItemDTO, _dto=ListItemDTO
        )
