from schemas.users import UserAuthDTO, UserDTO
from services.base import BaseService
from services.exceptions import InvalidCredentials
from core.security import check_password


class AuthService(BaseService):
    async def authenticate(self, email: str, password: str) -> UserDTO:
        user_with_password: UserAuthDTO | None = await self.uow.users.get_by_email_with_password(email)
        if user_with_password is None:
            self._log_info('Authentication failed: user not found')
            raise InvalidCredentials

        if user_with_password.deleted_at is not None:
            self._log_info('Authentication failed: user deleted', extra={'user_id': user_with_password.id})
            raise InvalidCredentials

        is_valid_password = await check_password(password, user_with_password.hashed_password)
        if not is_valid_password:
            self._log_info('Authentication failed: invalid password', extra={'user_id': user_with_password.id})
            raise InvalidCredentials

        return UserDTO(**user_with_password.model_dump())
