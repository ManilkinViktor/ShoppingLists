import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database.repositories.base import BaseRepository
from database.models import ShoppingListsOrm
from schemas.shopping_lists import ShoppingListDTO, ShoppingListAddDTO, ShoppingListRelItemDTO

class ShoppingListsRepository(
    BaseRepository[
        ShoppingListsOrm,
        ShoppingListAddDTO,
        ShoppingListDTO,
    ]):

    def __init__(self, _session: AsyncSession):
        super().__init__(
            _session,
            _model=ShoppingListsOrm, _add_dto=ShoppingListDTO, _dto=ShoppingListDTO
        )

    async def get_list_with_items(self, list_id: uuid.UUID) -> ShoppingListRelItemDTO | None:
        query = (select(ShoppingListsOrm)
                 .where(ShoppingListsOrm.id == list_id)
                 .options(selectinload(ShoppingListsOrm.items)))
        result = await self._session.execute(query)
        list_orm: ShoppingListsOrm | None = result.scalar_one_or_none()
        if list_orm:
            return ShoppingListRelItemDTO.model_validate(list_orm, from_attributes=True)
        return None