from typing import TYPE_CHECKING
import uuid
from database.models.workspace_members import Role
from pydantic import BaseModel

if TYPE_CHECKING:
    from schemas.workspaces import WorkspaceRelListDTO
    from schemas.users import UserDTO


class WorkspaceMemberDTO(BaseModel):
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    role: Role

class WorkspaceMemberRelWorkspaceDTO(WorkspaceMemberDTO):
    workspace: 'WorkspaceRelListDTO | None'

class WorkspaceMembersRelUserDTO(WorkspaceMemberDTO):
    user: 'UserDTO | None'