import uuid

from pydantic import BaseModel, Field

from core.enums import Role


class CreateInviteRequestDTO(BaseModel):
    role: Role
    max_uses: int | None = Field(default=None, ge=1)
    expires_in_hours: int = Field(default=24, ge=1, le=8760)


class JoinByInviteRequestDTO(BaseModel):
    code: uuid.UUID
