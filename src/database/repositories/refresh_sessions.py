import datetime
import uuid

from sqlalchemy import select, update, CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import RefreshSessionsOrm
from utils.datetime_utils import utc_now


class RefreshSessionsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, user_id: uuid.UUID, jti: uuid.UUID, expires_at: datetime.datetime) -> None:
        self._session.add(
            RefreshSessionsOrm(
                user_id=user_id,
                jti=jti,
                expires_at=expires_at,
            )
        )
        await self._session.flush()

    async def is_active(self, user_id: uuid.UUID, jti: uuid.UUID) -> bool:
        stmt = (
            select(RefreshSessionsOrm.id)
            .where(RefreshSessionsOrm.user_id == user_id)
            .where(RefreshSessionsOrm.jti == jti)
            .where(RefreshSessionsOrm.revoked_at.is_(None))
            .where(RefreshSessionsOrm.expires_at > utc_now())
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def revoke(self, user_id: uuid.UUID, jti: uuid.UUID) -> bool:
        stmt = (
            update(RefreshSessionsOrm)
            .where(RefreshSessionsOrm.user_id == user_id)
            .where(RefreshSessionsOrm.jti == jti)
            .where(RefreshSessionsOrm.revoked_at.is_(None))
            .values(revoked_at=utc_now())
        )
        result = await self._session.execute(stmt)
        answer: bool = False
        if isinstance(result, CursorResult):
            answer = bool(result.rowcount)
        return answer
