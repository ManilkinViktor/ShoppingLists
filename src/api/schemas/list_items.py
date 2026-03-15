import uuid

from pydantic import BaseModel, Field

from core.constants import FieldConstraints


class ListItemCreateRequestDTO(BaseModel):
    id: uuid.UUID
    name: str = Field(min_length=1, max_length=FieldConstraints.base_len)
    quantity: int = Field(gt=0, lt=FieldConstraints.quantity_border)
    unit: str | None = Field(max_length=FieldConstraints.base_len)
    category: str | None = Field(max_length=FieldConstraints.base_len)
    is_purchased: bool = Field(default=False)
