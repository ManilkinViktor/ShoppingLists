import uuid

from uuid_utils import uuid7
from pydantic import EmailStr
from redis.asyncio import Redis

from api.schemas.auth import VerifyCodeDTO, UserRegisterDTO
from core.config import settings
from core.security import check_password, generate_code, hash_code, hash_password
from database.uow import UnitOfWork
from schemas.users import UserAuthDTO, UserDTO, UserCreateAuthDTO
from services.base import BaseService
from services.exceptions import InvalidCredentials, EmailAlreadyExists


class AuthService(BaseService):
    def __init__(self, uow: UnitOfWork, redis: Redis) -> None:
        super().__init__(uow)
        self.redis = redis

    async def register(self, register_data: UserRegisterDTO):
        found_user: UserDTO = await self.uow.users.get_by(email=register_data.email)
        if found_user:
            self._log_info('registration failed email already exists', immediate=True)
            raise EmailAlreadyExists
        session_id = str(uuid.uuid4())
        code = generate_code()
        code_hash = hash_code(code)
        redis_key = f"verify:{session_id}"
        hashed_password = await hash_password(register_data.password)
        user_data = UserCreateAuthDTO(
            **register_data.model_dump(),
            hashed_password=hashed_password,
            id=str(uuid7())
        )
        await self.redis.hset(
            redis_key,
            mapping={
                "code_hash": code_hash,
                "attempts": 0,
                "user_data": user_data.model_dump()
            }
        )
        await self.redis.expire(redis_key, settings.VERIFY_EMAIL_EXPIRE_SECONDS)

        # await send_email()

        return session_id, VerifyCodeDTO(code=code)

    async def verify(self, verify_data: VerifyCodeDTO, session_id: str):
        redis_key = f'verify:{session_id}'
        stored = await self.redis.hgetall(redis_key)
        if not stored:
            self._log_info('Verify failed, code expired or not found')
            raise ValueError("Code expired or not found")
        attempts = int(stored.get('attempts', 0))
        if attempts >= settings.VERIFY_ATTEMPTS:
            await self.redis.delete(redis_key)
            self._log_info('Verify failed, too many attempts')
            raise ValueError("Too many attempts")
        if hash_code(verify_data.code) != stored.get('code_hash', None):
            await self.redis.hincrby(redis_key, "attempts", 1)
            self._log_info('Verify failed, invalid code')
            raise ValueError('Invalid code')
        user_data = UserCreateAuthDTO.model_validate(stored.get('user_data'))
        await self.redis.delete(redis_key)
        return user_data


    async def authenticate(self, email: str, password: str) -> UserDTO:
        user_with_password: UserAuthDTO | None = await self.uow.users.get_by_email_with_password(email)

        if user_with_password is None:
            self._log_info('Authentication failed: user not found', immediate=True)
            raise InvalidCredentials

        if user_with_password.deleted_at is not None:
            self._log_info('Authentication failed: user deleted', extra={'user_id': user_with_password.id}, immediate=True)
            raise InvalidCredentials

        is_valid_password = await check_password(password, user_with_password.hashed_password)
        if not is_valid_password:
            self._log_info('Authentication failed: invalid password', extra={'user_id': user_with_password.id}, immediate=True)
            raise InvalidCredentials

        return UserDTO(**user_with_password.model_dump())
