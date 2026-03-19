from pydantic import BaseModel

from core.enums import Role


class UpdateMemberRoleRequestDTO(BaseModel):
    role: Role
