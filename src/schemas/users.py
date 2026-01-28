from typing import Annotated, List, TYPE_CHECKING
from abc import ABC

from pydantic import EmailStr, Field

from schemas.mixins import UUIDMixinDTO, TimeStampMixinDTO
from core.constants import FieldConstraints

if TYPE_CHECKING:
    from schemas.workspace_members import WorkspaceMemberRelWorkspaceDTO

class UserBaseDTO(UUIDMixinDTO, ABC):
    name: str = Field(min_length=1, max_length=FieldConstraints.base_len)
    email: EmailStr


class UserDTO(UserBaseDTO, TimeStampMixinDTO):
    pass

password_field = Annotated[str, Field(min_length=FieldConstraints.min_password, max_length=FieldConstraints.base_len)]

class UserAddDTO(UserBaseDTO):
    password: password_field
    password_confirmation: password_field


class UserAuthDTO(UserDTO):
    hashed_password: str


class UserRelWorkspaceDTO(UserDTO):
    connected_workspaces: List['WorkspaceMemberRelWorkspaceDTO']
