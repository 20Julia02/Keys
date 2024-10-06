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
    is_taken = Column(Boolean, nullable=False, server_default="false")
    last_taken = Column(TIMESTAMP(timezone=True), nullable=True)
    last_returned = Column(TIMESTAMP(timezone=True), nullable=True)
    last_owner_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    issue_return_session_id = Column(Integer, ForeignKey("issue_return_session.id"), nullable=False)

    issue_return_session = relationship("IssueReturnSession")
    user = relationship("User")
    device = relationship("Device")


class TransactionType(enum.Enum):
    issue_dev = "issue_device"
    return_dev = "return_device"


class DeviceTransaction(Base):
    __tablename__ = "device_transaction"
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    device_code = Column(String, ForeignKey("device.code"), nullable=False)
    issue_return_session_id = Column(Integer, ForeignKey("issue_return_session.id"), nullable=False)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    entitled = Column(Boolean, nullable=True)

    device = relationship("Device")
    issue_return_session = relationship("IssueReturnSession")

    __table_args__ = (UniqueConstraint(
        "device_code", "issue_return_session_id", name="uix_device_session"),)


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


class SessionStatus(enum.Enum):
    in_progress = "in_progress"
    completed = "completed"
    rejected = "rejected"

# todo concierge who started and who accepted

class IssueReturnSession (Base):
    __tablename__ = "issue_return_session"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    concierge_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    start_time = Column(TIMESTAMP(timezone=True), nullable=False)
    end_time = Column(TIMESTAMP(timezone=True), nullable=True)
    status = Column(Enum(SessionStatus), nullable=False)


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
    device_transaction_id = Column(Integer, ForeignKey("device_transaction.id"), nullable=True)
    note = Column(String, nullable=False)

    device_transaction = relationship("DeviceTransaction")


class UserNote(Base):
    __tablename__ = "user_note"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    note = Column(String, nullable=False)

    user = relationship("User")
