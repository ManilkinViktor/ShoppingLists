import uuid
from typing import Annotated, TypeAlias

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.asyncio import Redis

from api.http_exceptions import unauthorized_credentials_http_exception
from core.security import decode_token
from database.uow import UnitOfWork
from schemas.users import UserDTO
from services.auth import AuthService
from services.users import UserService

UoWDep: TypeAlias = Annotated[UnitOfWork, Depends(UnitOfWork.get_with)]


def get_redis(request: Request):
    return request.state.redis

RedisDep: TypeAlias = Annotated[Redis, Depends(get_redis)]

AuthServiceDep: TypeAlias = Annotated[AuthService, AuthService(UoWDep, RedisDep)]
UserServiceDep: TypeAlias = Annotated[UserService, UserService(UoWDep)]

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
        uow: UoWDep,
) -> UserDTO:
    if credentials is None:
        raise unauthorized_credentials_http_exception()

    if credentials.scheme.lower() != 'bearer':
        raise unauthorized_credentials_http_exception()

    try:
        payload = decode_token(credentials.credentials)
    except jwt.PyJWTError as error:
        raise unauthorized_credentials_http_exception() from None

    token_type = payload.get('type')
    if token_type != 'access':
        raise unauthorized_credentials_http_exception()

    subject = payload.get('sub')
    if subject is None:
        raise unauthorized_credentials_http_exception()

    try:
        user_id = uuid.UUID(subject)
    except ValueError as error:
        raise unauthorized_credentials_http_exception() from None

    user = await uow.users.get(user_id)
    if user is None or user.deleted_at is not None:
        raise unauthorized_credentials_http_exception()

    return user


CurrentUser: TypeAlias = Annotated[UserDTO, Depends(get_current_user)]
