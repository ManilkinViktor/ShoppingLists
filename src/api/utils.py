from fastapi import APIRouter
from uuid_utils import uuid7

router = APIRouter(prefix='/utils', tags=['utils'])


@router.get('/uuid7')
async def get_uuid7() -> str:
    return str(uuid7())
