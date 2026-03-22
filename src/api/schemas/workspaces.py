from pydantic import BaseModel, Field

from core.constants import FieldConstraints
from schemas.mixins import UUIDMixinDTO


class WorkspaceVersionRequestDTO(BaseModel):
    workspace_version: int = Field(ge=0)


class WorkspaceCreateRequestDTO(UUIDMixinDTO):
    name: str = Field(min_length=1, max_length=FieldConstraints.BASE_LEN)
    description: str | None = Field(max_length=FieldConstraints.DESCRIPTION_LEN)


class WorkspacePatchRequestDTO(WorkspaceVersionRequestDTO):
    name: str | None = Field(default=None, min_length=1, max_length=FieldConstraints.BASE_LEN)
    description: str | None = Field(default=None, max_length=FieldConstraints.DESCRIPTION_LEN)


class WorkspaceDeleteRequestDTO(WorkspaceVersionRequestDTO):
    pass
