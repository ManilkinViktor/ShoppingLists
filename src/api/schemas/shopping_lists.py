from pydantic import Field

from api.schemas.list_items import ListItemCreateRequestDTO
from schemas.shopping_lists import ShoppingListCreateDTO


class ShoppingListCreateWithItemsDTO(ShoppingListCreateDTO):
    items: list[ListItemCreateRequestDTO] = Field(default_factory=list)
