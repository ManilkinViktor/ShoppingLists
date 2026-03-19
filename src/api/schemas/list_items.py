import uuid

from pydantic import BaseModel, Field

from api.schemas.workspaces import WorkspaceVersionRequestDTO
from core.constants import FieldConstraints


class ListItemCreateRequestDTO(BaseModel):
    id: uuid.UUID
    name: str = Field(min_length=1, max_length=FieldConstraints.BASE_LEN)
    quantity: int = Field(gt=0, lt=FieldConstraints.QUANTITY_BORDER)
    unit: str | None = Field(max_length=FieldConstraints.BASE_LEN)
    category: str | None = Field(max_length=FieldConstraints.BASE_LEN)
    is_purchased: bool = Field(default=False)


class ListItemPatchRequestDTO(BaseModel):
    id: uuid.UUID
    name: str | None = Field(default=None, min_length=1, max_length=FieldConstraints.BASE_LEN)
    delta_quantity: int | None = Field(
        default=None,
        gt=-FieldConstraints.QUANTITY_BORDER,
        lt=FieldConstraints.QUANTITY_BORDER,
        description='Additive delta to apply to current quantity',
    )
    unit: str | None = Field(default=None, max_length=FieldConstraints.BASE_LEN)
    category: str | None = Field(default=None, max_length=FieldConstraints.BASE_LEN)
    is_purchased: bool | None = None


class ListItemsCreateRequestDTO(WorkspaceVersionRequestDTO):
    items: list[ListItemCreateRequestDTO] = Field(default_factory=list)


class ListItemsPatchRequestDTO(WorkspaceVersionRequestDTO):
    items: list[ListItemPatchRequestDTO] = Field(default_factory=list)


class ListItemsDeleteRequestDTO(WorkspaceVersionRequestDTO):
    ids: list[uuid.UUID] = Field(default_factory=list)
