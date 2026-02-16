import bcrypt

from fastapi.concurrency import run_in_threadpool


def _hash_password_sync(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

async def hash_password(password: str) -> str:
    return await run_in_threadpool(_hash_password_sync, password)


def _check_password_sync(password: str, hashed: str):
    return bcrypt.checkpw(
        password.encode('utf-8'),
        hashed.encode('utf-8')
    )

async def check_password(password: str, hashed: str):
    return await run_in_threadpool(_check_password_sync, password, hashed)
