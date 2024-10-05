from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Enum, UniqueConstraint
from app.database import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import TIMESTAMP
import enum
from sqlalchemy.sql.expression import text


class TokenBlacklist(Base):
    __tablename__ = 'token_blacklist'
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    token = Column(String, unique=True, nullable=False)
    when_blacklisted = Column(TIMESTAMP(timezone=True),
                            nullable=False, server_default=text('now()'))


class DeviceVersion(enum.Enum):
    primary = "primary"
    backup = "backup"
    emergency = "emergency"


class DeviceType(enum.Enum):
    key = "key"
    microphone = "microphone"
    remote_controler = "remote_controler"


class Device(Base):
    __tablename__ = "device"
    code = Column(String, primary_key=True, unique=True, nullable=False)
    type = Column(Enum(DeviceType), nullable=False)
    room_id = Column(Integer, ForeignKey("room.id"), nullable=False)
    version = Column(Enum(DeviceVersion), nullable=False)
    entitled = Column(Boolean, nullable=True)
    is_taken = Column(Boolean, nullable=False, server_default="false")
    last_taken = Column(TIMESTAMP(timezone=True), nullable=True)
    last_returned = Column(TIMESTAMP(timezone=True), nullable=True)
    last_owner_id = Column(Integer, ForeignKey("user.id"), nullable=True)

    room = relationship("Room")
    user = relationship("User")

    __table_args__ = (UniqueConstraint(
        "type", "room_id", "version", name="uix_device"),)

class DeviceUnapproved(Base):
    __tablename__ = "device_unapproved"
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    device_code = Column(String, ForeignKey("device.code"), nullable=False)
    activity_id = Column(Integer, ForeignKey("activity.id"), nullable=False)
    entitled = Column(Boolean, nullable=False)
    is_taken = Column(Boolean, nullable=False, server_default="false")
    last_taken = Column(TIMESTAMP(timezone=True), nullable=True)
    last_returned = Column(TIMESTAMP(timezone=True), nullable=True)
    last_owner_id = Column(Integer, ForeignKey("user.id"), nullable=True)

    user = relationship("User")
    activity = relationship("Activity")
    device = relationship("Device")


class OperationType(enum.Enum):
    issue_dev = "issue_dev"
    return_dev = "return_dev"


class Operation(Base):
    __tablename__ = "device_activity"
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    device_code = Column(String, ForeignKey("device.code"), nullable=False)
    activity_id = Column(Integer, ForeignKey("activity.id"), nullable=False)
    operation_type = Column(Enum(OperationType), nullable=False)

    __table_args__ = (UniqueConstraint(
        "device_code", "activity_id", name="uix_device_activity"),)


class UserRole(enum.Enum):
    admin = "admin"
    concierge = "concierge"
    employee = "employee"
    student = "student"
    guest = "guest"


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    name = Column(String, nullable=False)
    surname = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    faculty = Column(String, nullable=True)
    photo_url = Column(String, nullable=True)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    card_code = Column(String, unique=True, nullable=False)

    __table_args__ = (UniqueConstraint(
        "email", "password", name="uix_user"),)


class ActivityStatus(enum.Enum):
    in_progress = "in progress"
    completed = "completed"
    rejected = "rejected"

# todo concierge who started and who accepted

class Activity (Base):
    __tablename__ = "activity"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    concierge_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    start_time = Column(TIMESTAMP(timezone=True), nullable=False)
    end_time = Column(TIMESTAMP(timezone=True), nullable=True)
    status = Column(Enum(ActivityStatus), nullable=False)


class UnauthorizedUser(Base):
    __tablename__ = "unauthorized_user"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    name = Column(String, nullable=False)
    surname = Column(String, nullable=False)
    id_concierge_who_accepted = Column(
        Integer, ForeignKey("user.id"), nullable=True)
    addition_time = Column(TIMESTAMP(timezone=True), nullable=False)
    additional_info = Column(String, nullable=True)

    concierge = relationship("User")


class Room(Base):
    __tablename__ = "room"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    number = Column(String, nullable=False, unique=True)


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
    activity_id = Column(Integer, ForeignKey("activity.id"), nullable=False)
    device_code = Column(String, ForeignKey("device.code"), nullable=False)
    note = Column(String, nullable=False)
    time = Column(TIMESTAMP(timezone=True), nullable=False)

    device = relationship("Device")
    activity = relationship("Activity")

    __table_args__ = (UniqueConstraint(
        "device_code", "activity_id", name="uix_device_activity_note"),)


class UserNote(Base):
    __tablename__ = "user_note"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    note = Column(String, nullable=False)
    time = Column(TIMESTAMP(timezone=True), nullable=False)

    user = relationship("User")
