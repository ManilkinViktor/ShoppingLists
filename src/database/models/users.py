from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String

from src.database.base import Base
from src.database.mixins import TimestampMixin


fix_length = 256


class UserOrm(Base, TimestampMixin):
    __tablename__ = 'users'

    name: Mapped[str] = mapped_column(String(fix_length))
    email: Mapped[str] = mapped_column(String(fix_length))
    hashed_password: Mapped[str] = mapped_column(String(fix_length))



