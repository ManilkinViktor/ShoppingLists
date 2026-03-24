import datetime
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, TIMESTAMP, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base
from database.mixins import UUIDMixin
from utils.datetime_utils import utc_now

if TYPE_CHECKING:
    from database.models import UsersOrm


class RefreshSessionsOrm(UUIDMixin, Base):
    __tablename__ = 'refresh_sessions'

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    jti: Mapped[uuid.UUID] = mapped_column(unique=True)
    expires_at: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(timezone=True))
    revoked_at: Mapped[datetime.datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True, default=None)
    created_at: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(timezone=True), default=utc_now)

    user: Mapped['UsersOrm'] = relationship(back_populates='refresh_sessions')

    __table_args__ = (
        Index('ix_refresh_sessions_user_active', 'user_id', 'revoked_at', 'expires_at'),
    )
