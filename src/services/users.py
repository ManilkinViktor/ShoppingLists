from core.security import hash_password
from services.base import BaseService
from services.exceptions import EmailAlreadyExists, ConflictUUID
from schemas.users import UserAddDTO, UserDTO, UserAuthDTO, UserBaseDTO


class UserService(BaseService):

    async def create(self, user_data: UserAddDTO) -> UserDTO:
        found_user: UserDTO | None = self.uow.users.get_by_filters_or(email=user_data.email, id=user_data.id)
        if found_user:
            if user_data.id == found_user.id:
                if self._same_users(found_user, user_data):
                    return found_user
                else:
                    self._log_info("Conflict uuid")
                    raise ConflictUUID
            self._log_info(f"User wasn't created: email already exists", extra={'user_id': user_data.id})
            raise EmailAlreadyExists
        hashed_password: str = await hash_password(user_data.password)
        user_auth_data: UserAuthDTO = UserAuthDTO(**user_data.model_dump(), hashed_password=hashed_password)
        await self.uow.users.add(user_auth_data)
        self._log_info(f"User was created", extra={'user_id': user_data.id})
        return UserDTO(**user_auth_data.model_dump())


    async def change_password(self, user: UserDTO, password: str):
        hashed_password = hash_password(password)
        await self.uow.users.update(user.id, hashed_password=hashed_password)
        self._log_info("Password was changed", extra={'user_id': user.id})

    @staticmethod
    def _same_users(first_user: UserBaseDTO, second_user: UserBaseDTO) -> bool:
        return (first_user.email == second_user.email
                and first_user.name == second_user.name)
















