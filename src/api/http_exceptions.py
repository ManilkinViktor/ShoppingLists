from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from services.exceptions import (
    ConflictUUID,
    DomainException,
    EmailAlreadyExists,
    EntityNotFound,
    InvalidCredentials,
    WorkspaceVersionMismatch,
)


def domain_to_http_exception(error: DomainException) -> HTTPException:
    if isinstance(error, EmailAlreadyExists):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={'code': error.error_code, 'message': error.public_message},
        )
    if isinstance(error, ConflictUUID):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={'code': error.error_code, 'message': error.public_message},
        )
    if isinstance(error, WorkspaceVersionMismatch):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={'code': error.error_code, 'message': error.public_message},
        )
    if isinstance(error, InvalidCredentials):
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={'code': error.error_code, 'message': error.public_message},
            headers={'WWW-Authenticate': 'Bearer'},
        )
    if isinstance(error, EntityNotFound):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'code': error.error_code, 'message': error.public_message},
        )
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={'code': error.error_code, 'message': error.public_message},
    )


def integrity_error_to_http_exception(error: IntegrityError) -> HTTPException:
    message = str(getattr(error, 'orig', error)).lower()
    if 'users_unique_email' in message or 'users.email' in message:
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={'code': EmailAlreadyExists.error_code, 'message': EmailAlreadyExists.public_message},
        )
    if 'users_pkey' in message:
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={'code': ConflictUUID.error_code, 'message': ConflictUUID.public_message},
        )
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={'code': 'INTERNAL_SERVER_ERROR', 'message': 'Internal server error'},
    )


def invalid_refresh_token_http_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={'code': 'INVALID_REFRESH_TOKEN', 'message': 'Invalid refresh token'},
        headers={'WWW-Authenticate': 'Bearer'},
    )
