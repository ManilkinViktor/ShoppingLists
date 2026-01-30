from typing import Annotated, TYPE_CHECKING
from abc import ABC

from pydantic import EmailStr, Field, model_validator, BaseModel

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


class PasswordWithConfirm(BaseModel):
    password: password_field
    password_confirmation: password_field

    @model_validator(mode='after')
    def validate_password_confirmation(self):
        if self.password != self.password_confirmation:
            raise ValueError("The passwords don't match")
        return self


class UserAddDTO(PasswordWithConfirm, UserBaseDTO):
    pass


class UserAuthDTO(UserDTO):
    hashed_password: str


class UserRelWorkspaceDTO(UserDTO):
    connected_workspaces: list['WorkspaceMemberRelWorkspaceDTO']
