from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories.base import BaseRepository
from database.models import ShoppingListsOrm
from schemas.shopping_lists import ShoppingListDTO

class ShoppingListsRepository(
    BaseRepository[
        ShoppingListsOrm,
        ShoppingListDTO,
        ShoppingListDTO,
    ]):

    def __init__(self, _session: AsyncSession):
        super().__init__(
            _session,
            _model=ShoppingListsOrm, _add_dto=ShoppingListDTO, _dto=ShoppingListDTO
        )


