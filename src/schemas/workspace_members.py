import datetime
from typing import TYPE_CHECKING
import uuid

from database.models.workspace_members import Role
from pydantic import BaseModel, field_validator
from utils.datetime_utils import validate_utc_timezone, validate_not_future_time

if TYPE_CHECKING:
    from schemas.workspaces import WorkspaceRelListDTO
    from schemas.users import UserDTO

class WorkspaceMemberCreateDTO(BaseModel):
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    role: Role


class WorkspaceMemberDTO(WorkspaceMemberCreateDTO):
    joined_at: datetime.datetime

    @field_validator('joined_at')
    @classmethod
    def validate_joined_at(cls, v: datetime.datetime) -> datetime.datetime:
        v = validate_utc_timezone(v)
        v = validate_not_future_time(v)
        return v


class WorkspaceMemberRelWorkspaceDTO(WorkspaceMemberDTO):
    workspace: 'WorkspaceRelListDTO | None'

class WorkspaceMembersRelUserDTO(WorkspaceMemberDTO):
    user: 'UserDTO | None'
