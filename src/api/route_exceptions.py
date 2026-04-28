from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from api.http_exceptions import (
    domain_to_http_exception,
    integrity_error_to_http_exception,
    internal_server_error_http_exception,
    validation_error_http_exception,
    ValidationError,
)
from core.logger import get_logger
from services.exceptions import DomainException

logger = get_logger(__name__)


def _http_exception_to_response(exception: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exception.status_code,
        content={'detail': exception.detail},
        headers=exception.headers,
    )


def _log_internal_exception(request: Request, exception: Exception, message: str) -> None:
    logger.error(
        message,
        extra={'path': str(request.url.path), 'method': request.method},
        exc_info=exception,
    )


async def handle_domain_exception(
        _request: Request,
        exception: Exception,
) -> JSONResponse:
    if not isinstance(exception, DomainException):
        raise TypeError('handle_domain_exception expects DomainException')
    return _http_exception_to_response(domain_to_http_exception(exception))


async def handle_integrity_error(
        request: Request,
        exception: Exception,
) -> JSONResponse:
    if not isinstance(exception, IntegrityError):
        raise TypeError('handle_integrity_error expects IntegrityError')
    http_exception = integrity_error_to_http_exception(exception)
    if http_exception.status_code >= 500:
        _log_internal_exception(
            request,
            exception,
            'Unhandled integrity error while processing request',
        )
    return _http_exception_to_response(http_exception)


async def handle_validation_error(
        _request: Request,
        exception: Exception,
) -> JSONResponse:
    if not isinstance(exception, ValidationError):
        raise TypeError('handle_validation_error expects ValidationError')
    return _http_exception_to_response(validation_error_http_exception(exception))


async def handle_unexpected_exception(
        request: Request,
        exception: Exception,
) -> JSONResponse:
    _log_internal_exception(
        request,
        exception,
        'Unhandled exception while processing request',
    )
    return _http_exception_to_response(internal_server_error_http_exception())


def register_route_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainException, handle_domain_exception)
    app.add_exception_handler(IntegrityError, handle_integrity_error)
    app.add_exception_handler(ValidationError, handle_validation_error)
    app.add_exception_handler(Exception, handle_unexpected_exception)
