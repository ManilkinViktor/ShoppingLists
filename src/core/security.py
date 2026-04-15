import datetime
import uuid
import secrets, hashlib
from typing import Any

import bcrypt
import jwt
from fastapi.concurrency import run_in_threadpool

from core.config import settings
from utils.datetime_utils import utc_now

def generate_code():
    return str(secrets.randbelow(1000000))


def hash_code(code: str):
    return hashlib.sha256(code.encode()).hexdigest()


def _hash_password_sync(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


async def hash_password(password: str) -> str:
    return await run_in_threadpool(_hash_password_sync, password)


def _check_password_sync(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(
        password.encode('utf-8'),
        hashed.encode('utf-8')
    )


async def check_password(password: str, hashed: str) -> bool:
    return await run_in_threadpool(_check_password_sync, password, hashed)


def _create_token(subject: uuid.UUID, token_type: str, expires_minutes: int) -> str:
    now = utc_now()
    payload = {
        'sub': str(subject),
        'type': token_type,
        'iat': now,
        'exp': now + datetime.timedelta(minutes=expires_minutes),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(subject: uuid.UUID, expires_minutes: int | None = None) -> str:
    lifetime = expires_minutes or settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    return _create_token(subject=subject, token_type='access', expires_minutes=lifetime)


def create_refresh_token(
        subject: uuid.UUID,
        expires_minutes: int | None = None,
        token_id: uuid.UUID | None = None,
) -> tuple[str, uuid.UUID, datetime.datetime]:
    lifetime = expires_minutes or settings.JWT_REFRESH_TOKEN_EXPIRE_MINUTES
    now = datetime.datetime.now(datetime.UTC)
    expires_at = now + datetime.timedelta(minutes=lifetime)
    jti = token_id or uuid.uuid4()
    payload = {
        'sub': str(subject),
        'type': 'refresh',
        'jti': str(jti),
        'iat': now,
        'exp': expires_at,
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, jti, expires_at


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )


def decode_access_token(token: str) -> dict[str, Any]:
    return decode_token(token)
