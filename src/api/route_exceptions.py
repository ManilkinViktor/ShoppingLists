import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from api.http_exceptions import (
    domain_to_http_exception,
    integrity_error_to_http_exception,
    internal_server_error_http_exception,
)
from services.exceptions import DomainException

logger = logging.getLogger(__name__)


def _http_exception_to_response(exception: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exception.status_code,
        content={'detail': exception.detail},
        headers=exception.headers,
    )


async def handle_domain_exception(
    _request: Request,
    exception: Exception,
) -> JSONResponse:
    if not isinstance(exception, DomainException):
        raise TypeError('handle_domain_exception expects DomainException')
    return _http_exception_to_response(domain_to_http_exception(exception))


async def handle_integrity_error(
    _request: Request,
    exception: Exception,
) -> JSONResponse:
    if not isinstance(exception, IntegrityError):
        raise TypeError('handle_integrity_error expects IntegrityError')
    return _http_exception_to_response(integrity_error_to_http_exception(exception))


async def handle_unexpected_exception(
    request: Request,
    exception: Exception,
) -> JSONResponse:
    logger.error(
        'Unhandled exception while processing request',
        extra={'path': str(request.url.path), 'method': request.method},
        exc_info=exception,
    )
    return _http_exception_to_response(internal_server_error_http_exception())


def register_route_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainException, handle_domain_exception)
    app.add_exception_handler(IntegrityError, handle_integrity_error)
    app.add_exception_handler(Exception, handle_unexpected_exception)
