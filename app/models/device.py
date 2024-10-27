from operator import indexOf
from sqlalchemy import Integer, and_, case, ForeignKey, String, UniqueConstraint, func, Index
from sqlalchemy.orm import relationship, mapped_column, Mapped, Session
import enum
from typing import Optional, List, TYPE_CHECKING
import datetime
from fastapi import HTTPException, status
from app import schemas
from app.models.base import Base, intpk, timestamp
from app.models.operation import DeviceOperation


if TYPE_CHECKING:
    from app.models.operation import UnapprovedOperation
    from app.models.permission import Permission
    from app.models.user import UserNote


class Room(Base):
    __tablename__ = "room"

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str] = mapped_column(String(20), unique=True, index=True)

    permissions: Mapped[List["Permission"]] = relationship(back_populates="room")
    devices: Mapped[List["Device"]] = relationship("Device", back_populates="room")

    @classmethod
    def get_rooms(cls, db: Session, room_number: Optional[str] = None) -> List["Room"]:
        query = db.query(Room)
        if room_number:
            query = query.filter(Room.number == room_number)
        rooms = query.all()
        if rooms is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="There is no room in database")
        return rooms

    @classmethod
    def get_room_id(cls, db: Session, room_id: int) -> "Room":
        room = db.query(Room).filter(Room.id == room_id).first()
        if not room:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Room with id: {room_id} doesn't exist")
        return room
    
    @classmethod
    def get_room_number(cls, db: Session, room_number: str) -> "Room":
        room = db.query(Room).filter(Room.number == room_number).first()
        if not room:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Room number: {room_number} doesn't exist")
        return room


class DeviceVersion(enum.Enum):
    primary = "podstawowa"
    backup = "zapasowa"


class DeviceType(enum.Enum):
    key = "klucz"
    microphone = "mikrofon"
    remote_controler = "pilot"

 
class Device(Base):
    __tablename__ = "device"
    id: Mapped[intpk]
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    dev_type: Mapped[DeviceType]
    room_id: Mapped[int] = mapped_column(ForeignKey("room.id", ondelete="RESTRICT", onupdate="RESTRICT"), index=True)
    dev_version: Mapped[DeviceVersion]

    room: Mapped["Room"] = relationship("Room", back_populates="devices")
    notes: Mapped[List["DeviceNote"]] = relationship(back_populates="device")
    device_operations: Mapped[List["DeviceOperation"]] = relationship(back_populates="device")
    unapproved_operations: Mapped[List["UnapprovedOperation"]] = relationship(back_populates="device")

    __table_args__ = (
        UniqueConstraint("dev_type", "room_id", "dev_version", name="uix_device"),
    )

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
            .outerjoin(last_operation_subq, Device.id == last_operation_subq.c.device_id)
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


class DeviceNote(Base):
    __tablename__ = "device_note"
    id: Mapped[intpk]
    device_id: Mapped[int] = mapped_column(ForeignKey("device.id", ondelete="CASCADE", onupdate="CASCADE"), index=True,)
    note: Mapped[str]
    timestamp: Mapped[timestamp]

    device: Mapped["Device"] = relationship(back_populates="notes")

    @classmethod
    def get_dev_notes(cls, db: Session) -> List["DeviceNote"]:
        notes = db.query(DeviceNote).all()
        if not notes:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="There are no device notes in database")

        return notes

    @classmethod
    def get_dev_notes_id(cls, db: Session, dev_id: int) -> List["DeviceNote"]:
        """Retrieve all device notes filtered by device ID or issue/return session ID."""
        notes = (db.query(DeviceNote)
                 .filter(DeviceNote.device_id == dev_id)
                 .order_by(DeviceNote.timestamp.asc())
                 .all())
        if not notes:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="There are no notes that match the given criteria")
        return notes

    @classmethod
    def create_dev_note(cls, db: Session, note_data: schemas.DeviceNote, commit: bool = True) -> "DeviceNote":
        """Create a new device note."""
        note_data_dict = note_data.model_dump()
        note_data_dict["timestamp"] = datetime.datetime.now()
        note = DeviceNote(**note_data_dict)
        db.add(note)
        if commit:
            try:
                db.commit()
                db.refresh(note)
            except Exception as e:
                db.rollback()
                raise e 
        return note

    @classmethod
    def update_device_note(cls, db: Session, note_id: int, note_data: schemas.NoteUpdate, commit: bool = True) -> "UserNote":

        note = db.query(DeviceNote).filter(DeviceNote.id == note_id).first()
        
        if not note:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Note with id {note_id} not found")

        note.note = note_data.note
        note.timestamp = datetime.datetime.now()

        if commit:
            try:
                db.commit()
                db.refresh(note)
            except Exception as e:
                db.rollback()
                raise e 

        return note
    
    @classmethod
    def delete_device_note(cls, db: Session, note_id: int):
        note = db.query(DeviceNote).filter(
            DeviceNote.id == note_id).first()

        if not note:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Note with id: {note_id} doesn't exist")

        db.delete(note)
        db.commit()