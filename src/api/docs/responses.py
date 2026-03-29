from collections.abc import Mapping
from typing import Any

from fastapi import HTTPException, status

from api.http_exceptions import (
    domain_to_http_exception,
    invalid_refresh_token_http_exception,
    unauthorized_credentials_http_exception,
)
from api.schemas.errors import ErrorResponseDTO, ErrorTextResponseDTO
from services.exceptions import (
    ConflictUUID,
    DuplicateWorkspaceSyncPayload,
    EmailAlreadyExists,
    InvalidCredentials,
    WorkspaceVersionMismatch,
)


def _model_for_exception(exception: HTTPException) -> type[ErrorResponseDTO | ErrorTextResponseDTO]:
    if isinstance(exception.detail, dict):
        return ErrorResponseDTO
    return ErrorTextResponseDTO


def _headers_for_exception(exception: HTTPException) -> dict[str, Any] | None:
    if not exception.headers:
        return None
    return {
        name: {'schema': {'type': 'string'}}
        for name in exception.headers
    }


def documented_http_exception(
    description: str,
    exception: HTTPException,
) -> dict[str, Any]:
    response: dict[str, Any] = {
        'model': _model_for_exception(exception),
        'description': description,
        'content': {
            'application/json': {
                'example': {
                    'detail': exception.detail,
                }
            }
        },
    }
    headers = _headers_for_exception(exception)
    if headers is not None:
        response['headers'] = headers
    return response


def documented_http_exceptions(
    description: str,
    examples: Mapping[str, HTTPException],
) -> dict[str, Any]:
    first_exception = next(iter(examples.values()))
    response: dict[str, Any] = {
        'model': _model_for_exception(first_exception),
        'description': description,
        'content': {
            'application/json': {
                'examples': {
                    name: {
                        'value': {
                            'detail': exception.detail,
                        }
                    }
                    for name, exception in examples.items()
                }
            }
        },
    }
    headers = _headers_for_exception(first_exception)
    if headers is not None:
        response['headers'] = headers
    return response


AUTH_REQUIRED_RESPONSE = {
    status.HTTP_401_UNAUTHORIZED: documented_http_exception(
        'Authentication is required.',
        unauthorized_credentials_http_exception(),
    )
}

INVALID_CREDENTIALS_RESPONSE = {
    status.HTTP_401_UNAUTHORIZED: documented_http_exception(
        'Email or password is invalid.',
        domain_to_http_exception(InvalidCredentials()),
    )
}

INVALID_REFRESH_TOKEN_RESPONSE = {
    status.HTTP_401_UNAUTHORIZED: documented_http_exception(
        'Refresh token is invalid or expired.',
        invalid_refresh_token_http_exception(),
    )
}

NOT_FOUND_RESPONSE = {
    status.HTTP_404_NOT_FOUND: documented_http_exception(
        'Requested entity was not found or is not accessible.',
        HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'code': 'ENTITY_NOT_FOUND', 'message': 'Entity not found'},
        ),
    )
}

UUID_CONFLICT_RESPONSE = {
    status.HTTP_409_CONFLICT: documented_http_exception(
        'Entity with the same UUID already exists.',
        domain_to_http_exception(ConflictUUID()),
    )
}

VERSION_CONFLICT_RESPONSE = {
    status.HTTP_409_CONFLICT: documented_http_exception(
        'Workspace version does not match the current server state.',
        domain_to_http_exception(WorkspaceVersionMismatch()),
    )
}

CREATE_CONFLICT_RESPONSE = {
    status.HTTP_409_CONFLICT: documented_http_exceptions(
        'Request conflicts with the current server state.',
        {
            'uuid_conflict': domain_to_http_exception(ConflictUUID()),
            'workspace_version_mismatch': domain_to_http_exception(WorkspaceVersionMismatch()),
        },
    )
}

USER_CREATE_CONFLICT_RESPONSE = {
    status.HTTP_409_CONFLICT: documented_http_exceptions(
        'Registration conflicts with existing user data.',
        {
            'email_already_exists': domain_to_http_exception(EmailAlreadyExists()),
            'uuid_conflict': domain_to_http_exception(ConflictUUID()),
        },
    )
}

SYNC_PAYLOAD_RESPONSE = {
    status.HTTP_400_BAD_REQUEST: documented_http_exception(
        'Sync payload must contain one entry per workspace.',
        domain_to_http_exception(DuplicateWorkspaceSyncPayload()),
    )
}
