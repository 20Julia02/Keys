from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import relationship, mapped_column, Mapped
from typing import Optional
import datetime
from app.models.base import Base, intpk, timestamp
from app.models.user import User
from app.models.device import Room


class TokenBlacklist(Base):
    __tablename__ = 'token_blacklist'

    id: Mapped[intpk]
    token: Mapped[str] = mapped_column(String(255), unique=True)
    added_at: Mapped[Optional[timestamp]]


class Permission(Base):
    __tablename__ = "permission"
    id: Mapped[intpk]
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    room_id: Mapped[int] = mapped_column(ForeignKey("room.id"))
    start_reservation: Mapped[datetime.datetime]
    end_reservation: Mapped[datetime.datetime]

    user: Mapped["User"] = relationship(back_populates="permissions")
    room: Mapped["Room"] = relationship(back_populates="permissions")