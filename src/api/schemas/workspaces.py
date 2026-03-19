from pydantic import BaseModel, Field

from schemas.mixins import UUIDMixinDTO
from core.constants import FieldConstraints


class WorkspaceVersionRequestDTO(BaseModel):
    workspace_version: int = Field(ge=0)


class WorkspaceCreateRequestDTO(UUIDMixinDTO):
    name: str = Field(min_length=1, max_length=FieldConstraints.base_len)
    description: str | None = Field(max_length=FieldConstraints.base_len)


class WorkspacePatchRequestDTO(WorkspaceVersionRequestDTO):
    name: str | None = Field(default=None, min_length=1, max_length=FieldConstraints.base_len)
    description: str | None = Field(default=None, max_length=FieldConstraints.base_len)


class WorkspaceDeleteRequestDTO(WorkspaceVersionRequestDTO):
    pass
