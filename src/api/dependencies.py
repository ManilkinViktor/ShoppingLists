import uuid
from typing import Annotated, TypeAlias

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.security import decode_token
from database.uow import UnitOfWork
from schemas.users import UserDTO

UoWDep: TypeAlias = Annotated[UnitOfWork, Depends(UnitOfWork.get_with)]

bearer_scheme = HTTPBearer(auto_error=False)


def _unauthorized_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )


async def get_current_user(
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
        uow: UoWDep,
) -> UserDTO:
    if credentials is None:
        raise _unauthorized_exception()

    if credentials.scheme.lower() != 'bearer':
        raise _unauthorized_exception()

    try:
        payload = decode_token(credentials.credentials)
    except jwt.PyJWTError as error:
        raise _unauthorized_exception() from None

    token_type = payload.get('type')
    if token_type != 'access':
        raise _unauthorized_exception()

    subject = payload.get('sub')
    if subject is None:
        raise _unauthorized_exception()

    try:
        user_id = uuid.UUID(subject)
    except ValueError as error:
        raise _unauthorized_exception() from None

    user = await uow.users.get(user_id)
    if user is None or user.deleted_at is not None:
        raise _unauthorized_exception()

    return user


CurrentUser: TypeAlias = Annotated[UserDTO, Depends(get_current_user)]
