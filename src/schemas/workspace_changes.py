import uuid
from enum import StrEnum

from pydantic import BaseModel, Field

from schemas.workspaces import WorkspaceDTO

class EntityType(StrEnum):
    Workspace

class Change(BaseModel):
    pass


class WorkspaceChangeAddDTO(BaseModel):
    workspace_id: uuid.UUID
    workspace_version: int = Field(ge=1)
    changes: list[Change]
