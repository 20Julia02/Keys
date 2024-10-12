from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Enum, UniqueConstraint, Index
from app.database import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import TIMESTAMP
import enum
from sqlalchemy.sql.expression import text


class TokenBlacklist(Base):
    __tablename__ = 'token_blacklist'
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    token = Column(String(255), unique=True, nullable=False)
    added_at = Column(TIMESTAMP(timezone=True),
                              nullable=False, server_default=text('now()'))

    __table_args__ = (Index('idx_when_blacklisted', added_at),)

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
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    dev_type = Column(Enum(DeviceType), nullable=False)
    room_id = Column(Integer, ForeignKey("room.id"), nullable=False)
    dev_version = Column(Enum(DeviceVersion), nullable=False)

    room = relationship("Room")
    notes = relationship("DeviceNote", back_populates="device")

    __table_args__ = (UniqueConstraint(
        "dev_type", "room_id", "dev_version", name="uix_device"),)
    

class OperationType(enum.Enum):
    issue_device = "issue_device"
    return_device = "return_device"


class UnapprovedOperation(Base):
    __tablename__ = "operation_unapproved"
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    device_id = Column(Integer, ForeignKey("device.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("session.id"), nullable=False)
    operation_type = Column(Enum(OperationType), nullable=False)
    entitled = Column(Boolean, nullable=True)
    timestamp = Column(TIMESTAMP(timezone=True), nullable=True)
    
    session = relationship("IssueReturnSession")
    device = relationship("Device")


class DeviceOperation(Base):
    __tablename__ = "device_operation"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    device_id = Column(Integer, ForeignKey("device.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("session.id"), nullable=False)
    operation_type = Column(Enum(OperationType), nullable=False)
    entitled = Column(Boolean, nullable=True)
    timestamp = Column(TIMESTAMP(timezone=True), nullable=True)

    device = relationship("Device")
    session = relationship("IssueReturnSession", back_populates="device_operations")


class BaseUser(Base):
    __tablename__ = "base_user"
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
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
    geodesy="Geodezji i Kartografii"


class User(BaseUser):
    __tablename__ = 'user'
    id = Column(Integer, ForeignKey('base_user.id'), primary_key=True)
    name = Column(String(50), nullable=False)
    surname = Column(String(50), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    faculty = Column(Enum(Faculty), nullable=True)
    photo_url = Column(String(255), nullable=True)
    email = Column(String(50), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    card_code = Column(String(255), nullable=False, unique=True)

    __mapper_args__ = {
        'polymorphic_identity': 'user'
    }


class UnauthorizedUser(BaseUser):
    __tablename__ = "unauthorized_user"
    id = Column(Integer, ForeignKey('base_user.id'), primary_key=True)
    name = Column(String(50), nullable=False)
    surname = Column(String(50), nullable=False)
    email = Column(String(50), nullable=False, unique=True)
    addition_time = Column(TIMESTAMP(timezone=True),
                           nullable=False, server_default=text('now()'))

    __mapper_args__ = {
        'polymorphic_identity': 'unauthorized_user'
    }


class SessionStatus(enum.Enum):
    in_progress = "in_progress"
    completed = "completed"
    rejected = "rejected"

# todo dodac relacje


class IssueReturnSession (Base):
    __tablename__ = "session"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id = Column(Integer, ForeignKey("base_user.id"), nullable=True)
    concierge_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    start_time = Column(TIMESTAMP(timezone=True), nullable=False)
    end_time = Column(TIMESTAMP(timezone=True), nullable=True)
    status = Column(Enum(SessionStatus), nullable=False)

    device_operations = relationship("DeviceOperation", back_populates="session")


class Room(Base):
    __tablename__ = "room"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    number = Column(String(10), nullable=False, unique=True)


class Permission(Base):
    __tablename__ = "permission"
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    room_id = Column(Integer, ForeignKey("room.id"), nullable=False)
    start_reservation = Column(TIMESTAMP(timezone=True), nullable=False)
    end_reservation = Column(TIMESTAMP(timezone=True), nullable=False)

    user = relationship("User")
    room = relationship("Room")


class DeviceNote(Base):
    __tablename__ = "device_note"
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    device_id = Column(Integer, ForeignKey("device.id"), nullable=True)
    note = Column(String, nullable=False)
    timestamp = Column(TIMESTAMP(timezone=True), nullable=False)

    device = relationship("Device", back_populates="notes")


class UserNote(Base):
    __tablename__ = "user_note"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id = Column(Integer, ForeignKey("base_user.id"), nullable=False)
    note = Column(String, nullable=False)
    timestamp = Column(TIMESTAMP(timezone=True), nullable=False)

    user = relationship("BaseUser")
