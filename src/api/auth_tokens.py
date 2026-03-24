import uuid

import jwt
from fastapi import Response

from api.http_exceptions import invalid_refresh_token_http_exception
from api.schemas.auth import TokenDTO
from core.config import settings
from core.security import create_access_token, decode_token
from schemas.users import UserDTO


def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key=settings.JWT_REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=settings.JWT_REFRESH_COOKIE_SECURE,
        samesite=settings.JWT_REFRESH_COOKIE_SAMESITE,
        max_age=settings.JWT_REFRESH_TOKEN_EXPIRE_MINUTES * 60,
        path='/auth',
    )


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.JWT_REFRESH_COOKIE_NAME,
        path='/auth',
    )


def build_access_token_response(user: UserDTO) -> TokenDTO:
    return TokenDTO(access_token=create_access_token(user.id))


def decode_refresh_token_or_raise(refresh_token: str) -> tuple[uuid.UUID, uuid.UUID]:
    decoded = decode_refresh_token(refresh_token)
    if decoded is None:
        raise invalid_refresh_token_http_exception()
    return decoded


def decode_refresh_token(refresh_token: str) -> tuple[uuid.UUID, uuid.UUID] | None:
    try:
        token_payload = decode_token(refresh_token)
        if token_payload.get('type') != 'refresh':
            return None

        subject = token_payload.get('sub')
        jti = token_payload.get('jti')
        if subject is None or jti is None:
            return None

        return uuid.UUID(subject), uuid.UUID(jti)
    except (jwt.PyJWTError, ValueError, TypeError):
        return None
