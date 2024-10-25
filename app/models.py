from sqlalchemy import Column, Integer, literal, and_, case, exists, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, aliased, relationship, mapped_column, Mapped, Session
from sqlalchemy.sql.sqltypes import TIMESTAMP
import enum
from typing import Optional, Literal, List
import datetime
from typing_extensions import Annotated
from fastapi import HTTPException, status
from app import schemas


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

    room: Mapped["Room"] = relationship("Room", back_populates="devices")
    notes: Mapped[List["DeviceNote"]] = relationship(back_populates="device")
    device_operations: Mapped[List["DeviceOperation"]] = relationship(back_populates="device")
    unapproved_operations: Mapped[List["UnapprovedOperation"]] = relationship(back_populates="device")

    __table_args__ = (UniqueConstraint(
        "dev_type", "room_id", "dev_version", name="uix_device"),)

    @classmethod
    def get_device_with_details(
        cls,
        db: Session,
        dev_type: Optional[str] = None,
        dev_version: Optional[str] = None,
        room_number: Optional[str] = None,
    ):
        last_operation_subq = DeviceOperation.last_operation_subquery(db)
        
        query = (
            db.query(
                cls.id,
                cls.code,
                cls.dev_type,
                cls.dev_version,
                Room.number.label("room_number"),
                case(
                    (func.count(DeviceNote.id) > 0, True),
                    else_=False
                ).label('has_note'),
                case(
                    (DeviceOperation.operation_type == "pobranie", True),
                    else_=False
                ).label('is_taken')
            )
            .join(Room, Device.room_id == Room.id)
            .outerjoin(last_operation_subq, Device.id == last_operation_subq.c.device_id)  # `.c` only on the subquery
            .outerjoin(DeviceOperation, and_(
                Device.id == DeviceOperation.device_id,
                DeviceOperation.timestamp == last_operation_subq.c.last_operation_timestamp
            ))
            .outerjoin(DeviceNote, Device.id == DeviceNote.device_id)
        )

        if dev_type:
            try:
                dev_type_enum = DeviceType[dev_type]
            except KeyError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail=f"Invalid device type: {dev_type}")
            query = query.filter(Device.dev_type == dev_type_enum)

        if dev_version:
            try:
                dev_version_enum = DeviceVersion[dev_version]
            except KeyError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail=f"Invalid device version: {dev_version}")
            query = query.filter(Device.dev_version == dev_version_enum)

        if room_number:
            query = query.filter(Room.number == room_number)

        query = query.group_by(
            Device.id, Room.number, DeviceOperation.operation_type
        )

        numeric_part = func.regexp_replace(Room.number, '\D+', '', 'g')
        text_part = func.regexp_replace(Room.number, '\d+', '', 'g')

        query = query.order_by(
            case(
                (numeric_part != '', func.cast(numeric_part, Integer)),
                else_=None
            ).asc(),
            case(
                (numeric_part == '', text_part),
                else_=None
            ).asc(),
            text_part.asc()
        )

        devices = query.all()

        if not devices:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="There are no devices that match the given criteria in the database")
        return devices
    

    @classmethod
    def get_by_id(cls, db: Session, dev_id: int) -> "Device":
        device = db.query(cls).filter(cls.id == dev_id).first()
        if not device:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                                detail=f"Device with id: {dev_id} doesn't exist")
        return device

    @classmethod
    def get_by_code(cls, db: Session, dev_code: str) -> "Device":
        device = db.query(cls).filter(cls.code == dev_code).first()
        if not device:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                                detail=f"Device with code: {dev_code} doesn't exist")
        return device

    @classmethod
    def create(cls, db: Session, device_data: schemas.DeviceCreate, commit: bool = True) -> "Device":
        new_device = cls(**device_data.model_dump())
        db.add(new_device)
        if commit:
            db.commit()
            db.refresh(new_device)
        return new_device


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


class BaseUser(Base):
    __tablename__ = "base_user"
    id: Mapped[intpk]
    user_type = Column(String(50))

    __mapper_args__ = {
        'polymorphic_on': user_type,
        'polymorphic_identity': 'base_user'
    }

    notes: Mapped[List["UserNote"]] = relationship(back_populates="user")
    sessions: Mapped[List["IssueReturnSession"]] = relationship(back_populates="user")


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

    permissions: Mapped[List["Permission"]] = relationship(back_populates="user")
    sessions: Mapped[List["IssueReturnSession"]] = relationship(back_populates="concierge")


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


class Room(Base):
    __tablename__ = "room"

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str] = mapped_column(String(20), unique=True)

    permissions: Mapped[List["Permission"]] = relationship(back_populates="room")
    devices: Mapped[List["Device"]] = relationship("Device", back_populates="room")


class Permission(Base):
    __tablename__ = "permission"
    id: Mapped[intpk]
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    room_id: Mapped[int] = mapped_column(ForeignKey("room.id"))
    start_reservation: Mapped[datetime.datetime]
    end_reservation: Mapped[datetime.datetime]

    user: Mapped["User"] = relationship(back_populates="permissions")
    room: Mapped["Room"] = relationship(back_populates="permissions")


class DeviceNote(Base):
    __tablename__ = "device_note"
    id: Mapped[intpk]
    device_id: Mapped[int] = mapped_column(ForeignKey("device.id"))
    note: Mapped[str]
    timestamp: Mapped[Optional[timestamp]]

    device: Mapped["Device"] = relationship(back_populates="notes")


class UserNote(Base):
    __tablename__ = "user_note"

    id: Mapped[intpk]
    user_id: Mapped[int] = mapped_column(ForeignKey("base_user.id"))
    note: Mapped[str]
    timestamp: Mapped[Optional[timestamp]]

    user: Mapped["BaseUser"] = relationship(back_populates="notes")
