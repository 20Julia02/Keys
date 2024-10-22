from sqlalchemy import Column, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, relationship, mapped_column, Mapped
from sqlalchemy.sql.sqltypes import TIMESTAMP
import enum
from typing import Optional, Literal
import datetime
from typing_extensions import Annotated


intpk = Annotated[int, mapped_column(primary_key=True)]
timestamp = Annotated[
    datetime.datetime,
    mapped_column(nullable=False, server_default=func.CURRENT_TIMESTAMP()),
]


class Base(DeclarativeBase):
    type_annotation_map = {
        datetime.datetime: TIMESTAMP(timezone=True),
    }


class TokenBlacklist(Base):
    __tablename__ = 'token_blacklist'
    id: Mapped[intpk]
    token: Mapped[str] = mapped_column(String(255), unique=True)
    added_at: Mapped[Optional[timestamp]]


class DeviceVersion(enum.Enum):
    primary = "podstawowa"
    backup = "zapasowa"
    emergency = "awaryjna"


class DeviceType(enum.Enum):
    key = "klucz"
    microphone = "mikrofon"
    remote_controler = "pilot"


class Device(Base):
    __tablename__ = "device"
    id: Mapped[intpk]
    code: Mapped[str] = mapped_column(String(50), unique=True)
    dev_type: Mapped[DeviceType]
    room_id: Mapped[int] = mapped_column(ForeignKey("room.id"))
    dev_version: Mapped[DeviceVersion]

    room = relationship("Room")
    notes = relationship("DeviceNote", back_populates="device")

    __table_args__ = (UniqueConstraint(
        "dev_type", "room_id", "dev_version", name="uix_device"),)


OperationType = Literal["pobranie", "zwrot"]


class UnapprovedOperation(Base):
    __tablename__ = "operation_unapproved"
    id: Mapped[intpk]
    device_id: Mapped[int] = mapped_column(ForeignKey("device.id"))
    session_id: Mapped[int] = mapped_column(ForeignKey("session.id"))
    operation_type: Mapped[OperationType]
    entitled: Mapped[bool]
    timestamp: Mapped[Optional[timestamp]]

    session = relationship("IssueReturnSession")
    device = relationship("Device")


class DeviceOperation(Base):
    __tablename__ = "device_operation"

    id: Mapped[intpk]
    device_id: Mapped[int] = mapped_column(ForeignKey("device.id"))
    session_id: Mapped[int] = mapped_column(ForeignKey("session.id"))
    operation_type: Mapped[OperationType]
    entitled: Mapped[bool]
    timestamp: Mapped[Optional[timestamp]]

    device = relationship("Device")
    session = relationship("IssueReturnSession",
                           back_populates="device_operations")


class BaseUser(Base):
    __tablename__ = "base_user"
    id: Mapped[intpk]
    user_type = Column(String(50))

    __mapper_args__ = {
        'polymorphic_on': user_type,
        'polymorphic_identity': 'base_user'
    }


class UserRole(enum.Enum):
    admin = "admin"
    concierge = "concierge"
    employee = "employee"
    student = "student"
    guest = "guest"


class Faculty(enum.Enum):
    geodesy = "Geodezji i Kartografii"


class User(BaseUser):
    __tablename__ = 'user'
    id: Mapped[intpk] = mapped_column(ForeignKey('base_user.id'))
    name: Mapped[str] = mapped_column(String(50))
    surname: Mapped[str] = mapped_column(String(50))
    role: Mapped[UserRole]
    faculty: Mapped[Optional[Faculty]]
    photo_url: Mapped[Optional[str]]
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str]
    card_code: Mapped[str] = mapped_column(unique=True)

    __mapper_args__ = {
        'polymorphic_identity': 'user'
    }


class UnauthorizedUser(BaseUser):
    __tablename__ = "unauthorized_user"
    id: Mapped[intpk] = mapped_column(ForeignKey('base_user.id'))
    name: Mapped[str] = mapped_column(String(50))
    surname: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(50), unique=True)
    added_at: Mapped[Optional[timestamp]]

    __mapper_args__ = {
        'polymorphic_identity': 'unauthorized_user'
    }


SessionStatus = Literal["w trakcie", "potwierdzona", "odrzucona"]


class IssueReturnSession (Base):
    __tablename__ = "session"

    id: Mapped[intpk]
    user_id: Mapped[int] = mapped_column(ForeignKey("base_user.id"))
    concierge_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    start_time: Mapped[datetime.datetime]
    end_time: Mapped[Optional[datetime.datetime]]
    status: Mapped[SessionStatus]

    device_operations = relationship(
        "DeviceOperation", back_populates="session")
    user = relationship("User", foreign_keys=[user_id])
    concierge = relationship("User", foreign_keys=[concierge_id])


class Room(Base):
    __tablename__ = "room"

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str] = mapped_column(String(20), unique=True)


class Permission(Base):
    __tablename__ = "permission"
    id: Mapped[intpk]
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    room_id: Mapped[int] = mapped_column(ForeignKey("room.id"))
    start_reservation: Mapped[datetime.datetime]
    end_reservation: Mapped[datetime.datetime]

    user = relationship("User")
    room = relationship("Room")


class DeviceNote(Base):
    __tablename__ = "device_note"
    id: Mapped[intpk]
    device_id: Mapped[int] = mapped_column(ForeignKey("device.id"))
    note: Mapped[str]
    timestamp: Mapped[Optional[timestamp]]

    device = relationship("Device", back_populates="notes")


class UserNote(Base):
    __tablename__ = "user_note"

    id: Mapped[intpk]
    user_id: Mapped[int] = mapped_column(ForeignKey("base_user.id"))
    note: Mapped[str]
    timestamp: Mapped[Optional[timestamp]]

    user = relationship("BaseUser")
