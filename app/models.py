from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Enum, UniqueConstraint
from .database import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import TIMESTAMP
import enum
from sqlalchemy.sql.expression import text


class TokenBlacklist(Base):
    __tablename__ = 'token_blacklist'
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    token = Column(String, unique=True, nullable=False)
    blacklisted_at = Column(TIMESTAMP(timezone=True),
                            nullable=False, server_default=text('now()'))


class DeviceVersion(enum.Enum):
    primary = "primary"
    backup = "backup"
    emergency = "emergency"


class DeviceType(enum.Enum):
    key = "key"
    microphone = "microphone"
    remote_controler = "remote_controler"


class Devices(Base):
    __tablename__ = "devices"
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    type = Column(Enum(DeviceType), nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    is_taken = Column(Boolean, nullable=False, server_default="false")
    last_taken = Column(TIMESTAMP(timezone=True), nullable=True)
    last_returned = Column(TIMESTAMP(timezone=True), nullable=True)
    last_owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    version = Column(Enum(DeviceVersion), nullable=False)
    code = Column(String, unique=True, nullable=False)
    owner = relationship("User")
    room = relationship("Room")

    __table_args__ = (UniqueConstraint(
        "type", "room_id", "version", name="uix_1"),)


class DevicesUnapproved(Base):
    __tablename__ = "devices_unapproved"
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    type = Column(Enum(DeviceType), nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    is_taken = Column(Boolean, nullable=False, server_default="false")
    last_taken = Column(TIMESTAMP(timezone=True), nullable=True)
    last_returned = Column(TIMESTAMP(timezone=True), nullable=True)
    last_owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    version = Column(Enum(DeviceVersion), nullable=False)
    code = Column(String, unique=True, nullable=False)
    owner = relationship("User")
    room = relationship("Room")

    __table_args__ = (UniqueConstraint(
        "type", "room_id", "version", name="uix_2"),)

class UserRole(enum.Enum):
    admin = "admin"
    concierge = "concierge"
    employee = "employee"
    student = "student"
    guest = "guest"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    name = Column(String, nullable=False)
    surname = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    faculty = Column(String, nullable=True)
    photo_url = Column(String, nullable=True)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    card_code = Column(String, unique=True, nullable=False)
    is_active = Column(Boolean, nullable=False, server_default="false")
    additional_info = Column(String, nullable=True)


class unauthorized_users(Base):
    __tablename__ = "unauthorized_users"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    name = Column(String, nullable=False)
    surname = Column(String, nullable=False)
    id_concierge_who_accepted = Column(
        Integer, ForeignKey("users.id"), nullable=True)
    additional_info = Column(String, nullable=True)

    concierge = relationship("User")


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    number = Column(String, nullable=False, unique=True)


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    start_reservation = Column(TIMESTAMP(timezone=True), nullable=False)
    end_reservation = Column(TIMESTAMP(timezone=True), nullable=False)

    user = relationship("User")
    room = relationship("Room")
