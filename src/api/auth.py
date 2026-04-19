from fastapi import APIRouter, Cookie, Response, status

from api.auth_tokens import build_access_token_response, clear_refresh_cookie, set_refresh_cookie, decode_refresh_token
from api.dependencies import CurrentUser, UoWDep, AuthServiceDep, UserServiceDep
from api.docs.responses import (
    AUTH_REQUIRED_RESPONSE,
    INVALID_CREDENTIALS_RESPONSE,
    INVALID_REFRESH_TOKEN_RESPONSE,
    USER_CREATE_CONFLICT_RESPONSE,
)
from api.schemas.auth import TokenDTO, UserLoginDTO, UserRegisterDTO, VerifyCodeDTO
from core.config import settings
from core.security import create_refresh_token
from schemas.users import UserDTO, UserCreateAuthDTO

router = APIRouter(prefix='/auth', tags=['auth'])


async def _set_email_verify_cookie(response: Response, session_id: str):
    response.set_cookie(
        key=settings.VERIFY_EMAIL_COOKIE_NAME,
        value=session_id,
        httponly=True,
        secure=settings.JWT_REFRESH_COOKIE_SECURE,
        samesite=settings.VERIFY_EMAIL_COOKIE_SAMESITE,
        max_age=settings.VERIFY_EMAIL_EXPIRE_SECONDS,
        path='/auth',
    )


@router.post(
    '/register',
    response_model=VerifyCodeDTO,
    status_code=status.HTTP_201_CREATED,
    summary='Register a new user',
    description='Creates a user account, issues an access token, and sets a refresh token cookie.',
    responses=USER_CREATE_CONFLICT_RESPONSE,
)
async def register(
        response: Response,
        payload: UserRegisterDTO,
        uow: UoWDep,
        auth_service: AuthServiceDep,
) -> VerifyCodeDTO:
    session_id, verify_code = await auth_service.register(payload)
    await _set_email_verify_cookie(response, session_id)
    await uow.commit()
    return verify_code


@router.post(
    '/verify',
    response_model=TokenDTO,
    status_code=status.HTTP_201_CREATED,
    summary='Send code to finish registration',
    description='Send 6-digit code to finish registration into verify-session'
)
async def verify(
        response: Response,
        payload: VerifyCodeDTO,
        auth_service: AuthServiceDep,
        user_service: UserServiceDep,
        uow: UoWDep,
        session_id: str | None = Cookie(default=None, alias=settings.VERIFY_EMAIL_COOKIE_NAME)
):
    if session_id is None:
        raise ValueError('Invalid verify session')
    user_data: UserCreateAuthDTO = await auth_service.verify(payload, session_id)
    user = await user_service.create(user_data)
    refresh_token, refresh_jti, refresh_expires_at = create_refresh_token(user.id)
    await uow.refresh_sessions.add(user.id, refresh_jti, refresh_expires_at)
    await uow.commit()

    set_refresh_cookie(response, refresh_token)
    return build_access_token_response(user)


@router.post(
    '/login',
    response_model=TokenDTO,
    summary='Log in with email and password',
    description='Authenticates a user, returns an access token, and sets a refresh token cookie.',
    responses=INVALID_CREDENTIALS_RESPONSE,
)
async def login(
        response: Response,
        payload: UserLoginDTO,
        uow: UoWDep,
        auth_service: AuthServiceDep,
) -> TokenDTO:
    user = await auth_service.authenticate(str(payload.email), payload.password)
    refresh_token, refresh_jti, refresh_expires_at = create_refresh_token(user.id)
    await uow.refresh_sessions.add(user.id, refresh_jti, refresh_expires_at)
    await uow.commit()

    set_refresh_cookie(response, refresh_token)
    return build_access_token_response(user)


@router.post(
    '/refresh',
    response_model=TokenDTO,
    summary='Refresh access token',
    description='Uses the refresh token cookie to rotate the refresh session and issue a new access token.',
    responses=INVALID_REFRESH_TOKEN_RESPONSE,
)
async def refresh(
        response: Response,
        uow: UoWDep,
        auth_service: AuthServiceDep,
        refresh_token: str | None = Cookie(default=None, alias=settings.JWT_REFRESH_COOKIE_NAME),
) -> TokenDTO:
    user, new_refresh_token = await auth_service.refresh_token(refresh_token)
    set_refresh_cookie(response, new_refresh_token)
    await uow.commit()
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
    responses=AUTH_REQUIRED_RESPONSE,
)
async def get_me(current_user: CurrentUser) -> UserDTO:
    return current_user
