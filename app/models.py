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
    primary = "primary"
    backup = "backup"
    emergency = "emergency"


class DeviceType(enum.Enum):
    key = "key"
    microphone = "microphone"
    remote_controler = "remote_controler"


class Device(Base):
    __tablename__ = "device"
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    dev_type = Column(Enum(DeviceType), nullable=False)
    room_id = Column(Integer, ForeignKey("room.id"), nullable=False)
    version = Column(Enum(DeviceVersion), nullable=False)
    is_taken = Column(Boolean, nullable=False, server_default="false")
    last_taken = Column(TIMESTAMP(timezone=True), nullable=True)
    last_returned = Column(TIMESTAMP(timezone=True), nullable=True)
    last_owner_id = Column(Integer, ForeignKey("base_user.id"), nullable=True)

    room = relationship("Room")
    user = relationship("BaseUser")

    __table_args__ = (UniqueConstraint(
        "dev_type", "room_id", "version", name="uix_device"),)
    
    def get_note_ids(self, session):
        # Zwraca listę ID notatek związanych z operacjami dla tego urządzenia
        query = (
            session.query(DeviceNote.id)
            .join(DeviceOperation, DeviceOperation.device_id == self.id)  # Łączymy z DeviceOperation
            .join(DeviceNote, DeviceNote.device_operation_id == DeviceOperation.id)  # Łączymy z DeviceNote
            .filter(DeviceOperation.device_id == self.id)  # Filtrujemy po urządzeniu
        )
        return [note_id[0] for note_id in query.all()]


class DeviceUnapproved(Base):
    __tablename__ = "device_unapproved"
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    device_id = Column(Integer, ForeignKey("device.id"), nullable=False)
    is_taken = Column(Boolean, nullable=False, server_default="false")
    last_taken = Column(TIMESTAMP(timezone=True), nullable=True)
    last_returned = Column(TIMESTAMP(timezone=True), nullable=True)
    last_owner_id = Column(Integer, ForeignKey("base_user.id"), nullable=True)
    issue_return_session_id = Column(Integer, ForeignKey("issue_return_session.id"), nullable=False)

    issue_return_session = relationship("IssueReturnSession")
    user = relationship("BaseUser")
    device = relationship("Device")


class OperationType(enum.Enum):
    issue_dev = "issue_device"
    return_dev = "return_device"


class DeviceOperation(Base):
    __tablename__ = "device_operation"
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    device_id = Column(Integer, ForeignKey("device.id"), nullable=False)
    issue_return_session_id = Column(Integer, ForeignKey("issue_return_session.id"), nullable=False)
    operation_type = Column(Enum(OperationType), nullable=False)
    entitled = Column(Boolean, nullable=True)

    device = relationship("Device")
    issue_return_session = relationship("IssueReturnSession", back_populates="device_operations")
    device_notes = relationship("DeviceNote", back_populates="device_operation")


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
    __tablename__ = "issue_return_session"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id = Column(Integer, ForeignKey("base_user.id"), nullable=True)
    concierge_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    start_time = Column(TIMESTAMP(timezone=True), nullable=False)
    end_time = Column(TIMESTAMP(timezone=True), nullable=True)
    status = Column(Enum(SessionStatus), nullable=False)

    device_operations = relationship("DeviceOperation", back_populates="issue_return_session")


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
    device_operation_id = Column(Integer, ForeignKey("device_operation.id"), nullable=True)
    note = Column(String, nullable=False)

    device_operation = relationship("DeviceOperation", back_populates="device_notes")

    @property
    def operation_user_id(self):
        if self.device_operation and self.device_operation.issue_return_session:
            return self.device_operation.issue_return_session.user_id
        return None
    
    @property
    def note_device(self):
        if self.device_operation:
            return self.device_operation.device
        return None


class UserNote(Base):
    __tablename__ = "user_note"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id = Column(Integer, ForeignKey("base_user.id"), nullable=False)
    note = Column(String, nullable=False)

    user = relationship("BaseUser")
