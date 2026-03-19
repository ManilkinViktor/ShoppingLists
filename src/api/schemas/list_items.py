import uuid

from pydantic import BaseModel, Field

from core.constants import FieldConstraints
from api.schemas.workspaces import WorkspaceVersionRequestDTO


class ListItemCreateRequestDTO(BaseModel):
    id: uuid.UUID
    name: str = Field(min_length=1, max_length=FieldConstraints.base_len)
    quantity: int = Field(gt=0, lt=FieldConstraints.quantity_border)
    unit: str | None = Field(max_length=FieldConstraints.base_len)
    category: str | None = Field(max_length=FieldConstraints.base_len)
    is_purchased: bool = Field(default=False)


class ListItemPatchRequestDTO(BaseModel):
    id: uuid.UUID
    name: str | None = Field(default=None, min_length=1, max_length=FieldConstraints.base_len)
    delta_quantity: int | None = Field(
        default=None,
        gt=-FieldConstraints.quantity_border,
        lt=FieldConstraints.quantity_border,
        description='Additive delta to apply to current quantity',
    )
    unit: str | None = Field(default=None, max_length=FieldConstraints.base_len)
    category: str | None = Field(default=None, max_length=FieldConstraints.base_len)
    is_purchased: bool | None = None


class ListItemsCreateRequestDTO(WorkspaceVersionRequestDTO):
    items: list[ListItemCreateRequestDTO] = Field(default_factory=list)


class ListItemsPatchRequestDTO(WorkspaceVersionRequestDTO):
    items: list[ListItemPatchRequestDTO] = Field(default_factory=list)


class ListItemsDeleteRequestDTO(WorkspaceVersionRequestDTO):
    ids: list[uuid.UUID] = Field(default_factory=list)
