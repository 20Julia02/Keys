from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import relationship, mapped_column, Mapped, Session
from typing import Optional, Literal, List, TYPE_CHECKING
import datetime
from fastapi import HTTPException, status
from app.models.base import Base, intpk, timestamp

# Użycie TYPE_CHECKING do opóźnionych importów
if TYPE_CHECKING:
    from app.models.user import BaseUser, User
    from app.models.device import Device
    

SessionStatus = Literal["w trakcie", "potwierdzona", "odrzucona"]


class IssueReturnSession(Base):
    __tablename__ = "session"

    id: Mapped[intpk]
    user_id: Mapped[int] = mapped_column(ForeignKey("base_user.id"))
    concierge_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    start_time: Mapped[datetime.datetime]
    end_time: Mapped[Optional[datetime.datetime]]
    status: Mapped[SessionStatus]

    device_operations: Mapped[List["DeviceOperation"]] = relationship(back_populates="session")
    unapproved_operations: Mapped[List["UnapprovedOperation"]] = relationship(back_populates="session")
    user: Mapped["BaseUser"] = relationship(foreign_keys=[user_id], back_populates="sessions")
    concierge: Mapped["User"] = relationship(foreign_keys=[concierge_id], back_populates="sessions")


OperationType = Literal["pobranie", "zwrot"]


class UnapprovedOperation(Base):
    __tablename__ = "operation_unapproved"
    id: Mapped[intpk]
    device_id: Mapped[int] = mapped_column(ForeignKey("device.id"))
    session_id: Mapped[int] = mapped_column(ForeignKey("session.id"))
    operation_type: Mapped[OperationType]
    entitled: Mapped[bool]
    timestamp: Mapped[Optional[timestamp]]

    session: Mapped["IssueReturnSession"] = relationship(back_populates="unapproved_operations")
    device: Mapped["Device"] = relationship(back_populates="unapproved_operations")


class DeviceOperation(Base):
    __tablename__ = "device_operation"

    id: Mapped[intpk]
    device_id: Mapped[int] = mapped_column(ForeignKey("device.id"))
    session_id: Mapped[Optional[int]] = mapped_column(ForeignKey("session.id"))
    operation_type: Mapped[OperationType]
    entitled: Mapped[bool]
    timestamp: Mapped[Optional[timestamp]]

    device: Mapped["Device"] = relationship(back_populates="device_operations")
    session: Mapped[Optional["IssueReturnSession"]] = relationship(back_populates="device_operations")

    @classmethod
    def last_operation_subquery(cls, db: Session):
        return (
            db.query(
                cls.device_id,
                func.max(cls.timestamp).label('last_operation_timestamp')
            )
            .group_by(cls.device_id)
            .subquery()
        )
    
    @classmethod
    def get_owned_by_user(cls, db: Session, user_id: int) -> List["DeviceOperation"]:
        last_operation_subquery = cls.last_operation_subquery(db)

        query = (
            db.query(cls)
            .join(last_operation_subquery,
                  (cls.device_id == last_operation_subquery.c.device_id) & 
                  (cls.timestamp == last_operation_subquery.c.last_operation_timestamp)
            )
            .join(IssueReturnSession, cls.session)
            .filter(IssueReturnSession.user_id == user_id)
            .filter(cls.operation_type == "pobranie")
            .order_by(cls.timestamp.asc())
        )

        operations = query.all()

        if not operations:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} doesn't have any devices"
            )

        return operations