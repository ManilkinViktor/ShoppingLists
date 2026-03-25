from fastapi import APIRouter, Cookie, Response, status
from sqlalchemy.exc import IntegrityError
from uuid_utils import uuid7

from api.auth_tokens import build_access_token_response, clear_refresh_cookie, set_refresh_cookie, \
    decode_refresh_token_or_raise, decode_refresh_token
from api.dependencies import CurrentUser, UoWDep
from api.http_exceptions import (
    domain_to_http_exception,
    integrity_error_to_http_exception,
    invalid_refresh_token_http_exception,
)
from api.schemas.auth import TokenDTO, UserLoginDTO, UserRegisterDTO
from core.config import settings
from core.security import create_refresh_token
from schemas.users import UserDTO, UserCreateDTO
from services.auth import AuthService
from services.exceptions import DomainException
from services.users import UserService

router = APIRouter(prefix='/auth', tags=['auth'])


@router.post(
    '/register',
    response_model=TokenDTO,
    status_code=status.HTTP_201_CREATED,
    summary='Register a new user',
    description='Creates a user account, issues an access token, and sets a refresh token cookie.',
)
async def register(
        response: Response,
        payload: UserRegisterDTO,
        uow: UoWDep,
) -> TokenDTO:
    user_service = UserService(uow)
    user_data = UserCreateDTO(id=str(uuid7()), **payload.model_dump())

    try:
        user = await user_service.create(user_data)
        refresh_token, refresh_jti, refresh_expires_at = create_refresh_token(user.id)
        await uow.refresh_sessions.add(user.id, refresh_jti, refresh_expires_at)
        await uow.commit()
    except DomainException as error:
        raise domain_to_http_exception(error) from None
    except IntegrityError as error:
        raise integrity_error_to_http_exception(error) from None

    set_refresh_cookie(response, refresh_token)
    return build_access_token_response(user)


@router.post(
    '/login',
    response_model=TokenDTO,
    summary='Log in with email and password',
    description='Authenticates a user, returns an access token, and sets a refresh token cookie.',
)
async def login(
        response: Response,
        payload: UserLoginDTO,
        uow: UoWDep,
) -> TokenDTO:
    auth_service = AuthService(uow)
    try:
        user = await auth_service.authenticate(str(payload.email), payload.password)
        refresh_token, refresh_jti, refresh_expires_at = create_refresh_token(user.id)
        await uow.refresh_sessions.add(user.id, refresh_jti, refresh_expires_at)
        await uow.commit()
    except DomainException as error:
        raise domain_to_http_exception(error) from None
    except IntegrityError as error:
        raise integrity_error_to_http_exception(error) from None

    set_refresh_cookie(response, refresh_token)
    return build_access_token_response(user)


@router.post(
    '/refresh',
    response_model=TokenDTO,
    summary='Refresh access token',
    description='Uses the refresh token cookie to rotate the refresh session and issue a new access token.',
)
async def refresh(
        response: Response,
        uow: UoWDep,
        refresh_token: str | None = Cookie(default=None, alias=settings.JWT_REFRESH_COOKIE_NAME),
) -> TokenDTO:
    if refresh_token is None:
        raise invalid_refresh_token_http_exception()

    user_id, refresh_jti = decode_refresh_token_or_raise(refresh_token)

    user = await uow.users.get(user_id)
    if user is None or user.deleted_at is not None:
        raise invalid_refresh_token_http_exception()

    is_active = await uow.refresh_sessions.is_active(user_id, refresh_jti)
    if not is_active:
        raise invalid_refresh_token_http_exception()

    was_revoked = await uow.refresh_sessions.revoke(user_id, refresh_jti)
    if not was_revoked:
        raise invalid_refresh_token_http_exception()

    try:
        new_refresh_token, new_refresh_jti, new_refresh_expires_at = create_refresh_token(user.id)
        await uow.refresh_sessions.add(user.id, new_refresh_jti, new_refresh_expires_at)
        await uow.commit()
    except IntegrityError as error:
        raise integrity_error_to_http_exception(error) from None

    set_refresh_cookie(response, new_refresh_token)
    return build_access_token_response(user)


@router.post(
    '/logout',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Log out current session',
    description='Clears the refresh token cookie and revokes the current refresh session when possible.',
)
async def logout(
        response: Response,
        uow: UoWDep,
        refresh_token: str | None = Cookie(default=None, alias=settings.JWT_REFRESH_COOKIE_NAME),
) -> None:
    clear_refresh_cookie(response)

    if refresh_token is None:
        return

    decoded = decode_refresh_token(refresh_token)
    if decoded is None:
        return

    user_id, refresh_jti = decoded
    was_revoked = await uow.refresh_sessions.revoke(user_id, refresh_jti)
    if was_revoked:
        await uow.commit()


@router.get(
    '/me',
    response_model=UserDTO,
    summary='Get current user profile',
    description='Returns the authenticated user resolved from the bearer access token.',
)
async def get_me(current_user: CurrentUser) -> UserDTO:
    return current_user
