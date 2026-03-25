from fastapi import APIRouter
from uuid_utils import uuid7

router = APIRouter(prefix='/utils', tags=['utils'])


@router.get(
    '/uuid7',
    summary='Generate UUID v7',
    description='Returns a new UUID v7 value for manual testing and request preparation.',
)
async def get_uuid7() -> str:
    return str(uuid7())
