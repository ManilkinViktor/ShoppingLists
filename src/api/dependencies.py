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
from services.shopping_lists import ShoppingListsService
from services.users import UserService
from services.workspace_invites import WorkspaceInviteService
from services.workspace_members import WorkspaceMembersService
from services.workspace_sync import WorkspaceSyncService
from services.workspaces import WorkspacesService

UoWDep: TypeAlias = Annotated[UnitOfWork, Depends(UnitOfWork.get_with)]


def get_redis(request: Request):
    return request.app.state.redis


RedisDep: TypeAlias = Annotated[Redis, Depends(get_redis)]


def get_user_service(uow: UoWDep):
    return UserService(uow)


def get_auth_service(uow: UoWDep, redis: RedisDep):
    return AuthService(uow, redis)


def get_shopping_lists_service(uow: UoWDep):
    return ShoppingListsService(uow)


def get_workspace_service(uow: UoWDep):
    return WorkspacesService(uow)


def get_workspace_sync_service(uow: UoWDep):
    return WorkspaceSyncService(uow)


def get_workspace_members_service(uow: UoWDep):
    return WorkspaceMembersService(uow)


def get_workspace_invites_service(uow: UoWDep):
    return WorkspaceInviteService(uow)


AuthServiceDep: TypeAlias = Annotated[AuthService, Depends(get_auth_service)]
UserServiceDep: TypeAlias = Annotated[UserService, Depends(get_user_service)]
ShoppingListsServiceDep: TypeAlias = Annotated[ShoppingListsService, Depends(get_shopping_lists_service)]
WorkspacesServiceDep: TypeAlias = Annotated[WorkspacesService, Depends(get_workspace_service)]
WorkspaceSyncServiceDep: TypeAlias = Annotated[WorkspaceSyncService, Depends(get_workspace_sync_service)]
WorkspaceMembersServiceDep: TypeAlias = Annotated[WorkspaceMembersService, Depends(get_workspace_members_service)]
WorkspaceInviteServiceDep: TypeAlias = Annotated[WorkspaceInviteService, Depends(get_workspace_invites_service)]

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
