import datetime
import uuid

from pydantic import BaseModel, Field

from core.enums import Role


class WorkspaceInviteCreateDTO(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    role: Role
    expires_at: datetime.datetime
    max_uses: int | None = Field(default=None, ge=1)


class WorkspaceInviteDTO(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    role: Role
    created_at: datetime.datetime
    expires_at: datetime.datetime
    max_uses: int | None
    current_uses: int
    is_active: bool


class InviteCodeResponseDTO(BaseModel):
    code: uuid.UUID
    role: Role
    expires_at: datetime.datetime
    max_uses: int | None
