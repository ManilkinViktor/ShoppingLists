from typing import Annotated, List, TYPE_CHECKING

from pydantic import EmailStr, Field

from schemas.mixins import UUIDMixinDTO, TimeStampMixinDTO
from core.constants import FieldConstraints

if TYPE_CHECKING:
    from schemas.workspace_members import WorkspaceMemberRelWorkspaceDTO


class UserDTO(UUIDMixinDTO, TimeStampMixinDTO):
    name: str = Field(min_length=1, max_length=FieldConstraints.base_len)
    email: EmailStr


password_field = Annotated[str, Field(min_length=5, max_length=FieldConstraints.base_len)]

class UserAddDTO(UserDTO):
    password: password_field
    password_confirmation: password_field


class UserAuthDTO(UserDTO):
    hashed_password: str


class UserRelWorkspaceDTO(UserDTO):
    connected_workspaces: List['WorkspaceMemberRelWorkspaceDTO']
