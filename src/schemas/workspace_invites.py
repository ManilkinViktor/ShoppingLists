import datetime
import uuid

from pydantic import BaseModel, Field

from core.enums import Role


class WorkspaceInviteCreateDTO(BaseModel):
    workspace_id: uuid.UUID
    role: Role
    max_uses: int | None = Field(default=None, ge=1)
    expires_in_hours: int = Field(default=24, ge=1)


class WorkspaceInviteDTO(BaseModel):
    id: str
    workspace_id: uuid.UUID
    role: Role
    created_at: datetime.datetime
    expires_at: datetime.datetime
    max_uses: int | None
    current_uses: int
    is_active: bool


class InviteCodeResponseDTO(BaseModel):
    code: str
    role: Role
    expires_at: datetime.datetime
    max_uses: int | None
