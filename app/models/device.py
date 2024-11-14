from sqlalchemy import Integer, and_, case, ForeignKey, String, UniqueConstraint, func, TIMESTAMP
from sqlalchemy.orm import Mapped, relationship, mapped_column, Session
import enum
import datetime
from fastapi import HTTPException, status
from app.models.base import Base
from app import schemas
from app.models.operation import UserSession, DeviceOperation
from app.models.user import User
from typing import Optional, List, Literal
from app.config import logger


class Room(Base):
    __tablename__ = "room"

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str] = mapped_column(String(20), unique=True, index=True)

    permissions = relationship("Permission", back_populates="room")
    devices = relationship("Device", back_populates="room")

    @classmethod
    def get_rooms(cls,
                  db: Session,
                  room_number: Optional[str] = None) -> List["Room"]:
        """
        Retrieves a list of rooms from the database. If `room_number` is specified, 
        only returns the room with the matching number.

        Args:
            db (Session): The database session.
            room_number (str, optional): The room number to filter by (if provided).

        Returns:
            List[Room]: A list of Room objects that match the criteria.

        Raises:
            HTTPException: If no rooms are found in the database.
        """
        logger.info("Fetching rooms from the database.")
        logger.debug(f"Room filter applied: room_number={room_number}")

        query = db.query(Room)
        if room_number:
            query = query.filter(Room.number == room_number)
        rooms = query.all()
        if not rooms:
            logger.warning(f"No rooms found with number: '{room_number}'"
                           if room_number else "No rooms found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="No rooms found")

        logger.debug(f"Rooms found: {rooms}")
        return rooms

    @classmethod
    def get_room_id(cls,
                    db: Session,
                    room_id: int) -> "Room":
        """
        Retrieves a room by its unique ID.

        Args:
            db (Session): The database session.
            room_id (int): The unique ID of the room.

        Returns:
            Room: The Room object with the specified ID.

        Raises:
            HTTPException: If no room with the given ID exists.
        """
        logger.info(f"Retrieving room by ID: {room_id}")

        room = db.query(Room).filter(Room.id == room_id).first()
        if not room:
            logger.warning(f"Room with ID {room_id} not found.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Room with id: {room_id} not found")
        logger.debug(f"Room retrieved: {room}")
        return room

    @classmethod
    def create_room(cls,
                    db: Session,
                    room_data: schemas.Room,
                    commit: Optional[bool] = True) -> "Room":
        """
        Creates a new room in the database.

        Args:
            db (Session): The database session.
            room_data (schemas.RoomCreate): Data required to create the new room.
            commit (bool, optional): Whether to commit the transaction immediately. Default is True.

        Returns:
            Room: The newly created Room object.

        Raises:
            HTTPException: If a room with the specified number already exists.
            Exception: For any issues during the commit.
        """
        logger.info("Creating a new room.")
        logger.debug(f"Room data: {room_data}")

        if db.query(Room).filter_by(number=room_data.number).first():
            logger.warning(
                f"Attempted to create room with duplicate number '{room_data.number}'.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Room with number '{room_data.number}' already exists."
            )

        new_room = Room(number=room_data.number)
        db.add(new_room)

        if commit:
            try:
                db.commit()
                logger.info(
                    f"Room with number '{room_data.number}' created successfully.")
            except Exception as e:
                db.rollback()
                logger.error(
                    f"Error while creating room with number '{room_data.number}': {e}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail="An internal error occurred while creating room.")

        logger.debug(f"New room added to the database: {new_room}")
        return new_room

    @classmethod
    def update_room(cls,
                    db: Session,
                    room_id: int,
                    room_data: schemas.Room,
                    commit: Optional[bool] = True) -> "Room":
        """
        Updates an existing room in the database.

        Args:
            db (Session): The database session.
            room_id (int): The ID of the room to update.
            room_data (schemas.RoomUpdate): Data for updating the room.
            commit (bool, optional): Whether to commit the transaction immediately. Default is True.

        Returns:
            Room: The updated Room object.

        Raises:
            HTTPException: If the room is not found or a room with the new number already exists.
            Exception: For any issues during the commit.
        """
        logger.info(f"Updating room with ID: {room_id}")
        logger.debug(f"New room data: {room_data}")

        room = db.query(Room).filter(Room.id == room_id).first()
        if not room:
            logger.warning(f"Room with ID {room_id} not found for update.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Room with id: {room_id} not found")

        if room_data.number != room.number:
            if db.query(Room).filter(Room.number == room_data.number).first():
                logger.warning(
                    f"Attempted to update room with duplicate number '{room_data.number}'.")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Room with number '{
                        room_data.number}' already exists."
                )
            room.number = room_data.number
            logger.debug(f"Room number updated to '{room_data.number}'")

        if commit:
            try:
                db.commit()
                logger.info(f"Room with ID {room_id} updated successfully.")
            except Exception as e:
                db.rollback()
                logger.error(f"Error updating room ID {room_id}: {e}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail=f"An internal error occurred while updating room")
        logger.debug(f"Updated room in the database: {room}")
        return room

    @classmethod
    def delete_room(cls,
                    db: Session,
                    room_id: int,
                    commit: Optional[bool] = True) -> bool:
        """
        Deletes a room by its ID from the database.

        Args:
            db (Session): The database session.
            room_id (int): The ID of the room to delete.
            commit (bool, optional): Whether to commit the transaction immediately. Default is True.

        Returns:
            bool: True if the room was successfully deleted.

        Raises:
            HTTPException: If the room with the given ID does not exist.
            Exception: For any issues during the commit.
        """
        logger.info(f"Deleting room with ID: {room_id}")

        room = db.query(Room).filter(Room.id == room_id).first()
        if not room:
            logger.warning(f"Room with ID {room_id} not found for deletion.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Room with id: {room_id} doesn't exist")
        db.delete(room)
        if commit:
            try:
                db.commit()
                logger.info(f"Room with ID {room_id} deleted successfully.")
            except Exception as e:
                db.rollback()
                logger.error(f"Error deleting room ID {room_id}: {e}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail=f"An internal error occurred while deleting room")
        return True


class DeviceVersion(enum.Enum):
    podstawowa = "podstawowa"
    zapasowa = "zapasowa"


class DeviceType(enum.Enum):
    klucz = "klucz"
    mikrofon = "mikrofon"
    pilot = "pilot"


class Device(Base):
    __tablename__ = "device"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    dev_type: Mapped[DeviceType]
    room_id: Mapped[int] = mapped_column(ForeignKey(
        "room.id", ondelete="RESTRICT", onupdate="RESTRICT"), index=True)
    dev_version: Mapped[DeviceVersion]

    room = relationship("Room", back_populates="devices")
    notes = relationship(
        "DeviceNote", back_populates="device")
    device_operations = relationship(
        "DeviceOperation", back_populates="device")
    unapproved_operations = relationship(
        "UnapprovedOperation", back_populates="device")

    __table_args__ = (
        UniqueConstraint("dev_type",
                         "dev_version", name="uix_type_version"),
    )

    @classmethod
    def get_dev_with_details(
        cls,
        db: Session,
        dev_type: Optional[Literal["klucz", "mikrofon", "pilot"]] = None,
        dev_version: Optional[Literal["podstawowa", "zapasowa"]] = None,
        room_number: Optional[str] = None
    ):
        """
        Retrieves detailed information for devices, including fields from related tables such as Room and User.
        This includes device type, version, room number, ownership status, and any associated notes.

        Args:
            db (Session): The database session.
            dev_type (str, optional): The type of device to filter by.
            dev_version (str, optional): The version of the device to filter by.
            room_number (str, optional): The room number to filter by.

        Returns:
            List[dict]: A list of dictionaries containing selected fields from Device, Room, User, and related tables.

        Raises:
            HTTPException: If no records match the given criteria.
        """
        logger.info("Retrieving devices with detailed information.")
        logger.debug(
            f"Filter parameters - dev_type: {dev_type}, dev_version: {dev_version}, room_number: {room_number}")

        last_operation_subq = DeviceOperation.last_operation_subquery(db=db)

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
                ).label('is_taken'),
                case(
                    (DeviceOperation.operation_type == "pobranie", User.name),
                    else_=None
                ).label("owner_name"),
                case(
                    (DeviceOperation.operation_type == "pobranie", User.surname),
                    else_=None
                ).label("owner_surname")
            )
            .join(Room, Device.room_id == Room.id)
            .outerjoin(last_operation_subq, Device.id == last_operation_subq.c.device_id)
            .outerjoin(DeviceOperation, and_(
                Device.id == DeviceOperation.device_id,
                DeviceOperation.timestamp == last_operation_subq.c.last_operation_timestamp
            ))
            .outerjoin(UserSession, DeviceOperation.session_id == UserSession.id)
            .outerjoin(User, User.id == UserSession.user_id)
            .outerjoin(DeviceNote, Device.id == DeviceNote.device_id)
            .group_by(
                cls.id, cls.code, cls.dev_type, cls.dev_version, Room.number,
                DeviceOperation.operation_type, User.name, User.surname
            )
        )

        if dev_type:
            logger.debug(f"Applying filter for dev_type: {dev_type}")
            query = query.filter(Device.dev_type == dev_type)

        if dev_version:
            logger.debug(f"Applying filter for dev_version: {dev_version}")
            query = query.filter(Device.dev_version == dev_version)

        if room_number:
            logger.debug(f"Applying filter for room_number: {room_number}")
            query = query.filter(Room.number == room_number)

        query = query.group_by(
            Device.id, Room.number, DeviceOperation.operation_type, User.name, User.surname
        )

        numeric_part = func.regexp_replace(Room.number, r'\D+', '', 'g')
        text_part = func.regexp_replace(Room.number, r'\d+', '', 'g')

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
        if len(devices) == 0:
            logger.warning("No devices found matching the specified criteria.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="No devices found matching criteria")

        logger.debug(f"Devices found: {devices}")
        return devices

    @classmethod
    def get_dev_by_id(cls,
                      db: Session,
                      dev_id: int) -> "Device":
        """
        Retrieves a device by its unique ID.

        Args:
            db (Session): The database session.
            dev_id (int): The unique ID of the device.

        Returns:
            Device: The Device object with the specified ID.

        Raises:
            HTTPException: If no device with the given ID exists.
        """
        logger.info(f"Attempting to retrieve device with ID: {dev_id}")
        device = db.query(cls).filter(cls.id == dev_id).first()
        if not device:
            logger.warning(f"Device with ID {dev_id} not found.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Device with id: {dev_id} not found")
        logger.debug(f"Device retrieved: {device}")
        return device

    @classmethod
    def get_dev_by_code(cls,
                        db: Session,
                        dev_code: str) -> "Device":
        """
        Retrieves a device by its unique code.

        Args:
            db (Session): The database session.
            dev_code (str): The unique code of the device.

        Returns:
            Device: The Device object with the specified code.

        Raises:
            HTTPException: If no device with the given code exists.
        """
        logger.info(f"Attempting to retrieve device with code: {dev_code}")

        device = db.query(cls).filter(cls.code == dev_code).first()
        if not device:
            logger.warning(f"Device with code {dev_code} not found.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Device with code: {dev_code} not found")

        logger.debug(f"Device retrieved: {device}")
        return device

    @classmethod
    def create_dev(cls,
                   db: Session,
                   device_data: schemas.DeviceCreate,
                   commit: Optional[bool] = True) -> "Device":
        """
        Creates a new device in the database.

        Args:
            db (Session): The database session.
            device_data (schemas.DeviceCreate): The data for creating the device.
            commit (bool, optional): Whether to commit the transaction after adding the device.

        Returns:
            Device: The created Device object.
        """
        logger.info("Creating a new device.")
        logger.debug(f"Device data provided: {device_data}")

        new_device = cls(**device_data.model_dump())
        db.add(new_device)

        if commit:
            try:
                db.commit()
                logger.info("Device created and committed to the database.")
            except Exception as e:
                db.rollback()
                logger.error(
                    f"Error while creating device: {e}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail=f"An internal error occurred while creating device")

        logger.debug(f"New device added to the database: {new_device}")
        return new_device

    @classmethod
    def update_dev(cls,
                   db: Session,
                   dev_id: int,
                   device_data: schemas.DeviceCreate,
                   commit: Optional[bool] = True) -> "Device":
        """
        Updates an existing device in the database.

        Args:
            db (Session): The database session.
            dev_id (int): The unique ID of the device to update.
            device_data (schemas.DeviceUpdate): The data for updating the device.
            commit (bool, optional): Whether to commit the transaction after updating the device.

        Returns:
            Device: The updated Device object.

        Raises:
            HTTPException: If the device with the given ID does not exist.
        """
        logger.info(f"Attempting to update device with ID: {dev_id}")
        logger.debug(f"New device data: {device_data}")

        device = cls.get_dev_by_id(db, dev_id)
        for key, value in device_data.model_dump().items():
            setattr(device, key, value)

        if commit:
            try:
                db.commit()
                logger.info(f"Device with ID {dev_id} updated successfully.")
            except Exception as e:
                logger.error(
                    f"Error while updating device with ID {dev_id}: {e}")
                db.rollback()
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail=f"An internal error occurred while updating device")

        logger.debug(f"Updated device in the database: {device}")
        return device

    @classmethod
    def delete_dev(cls,
                   db: Session,
                   dev_id: int,
                   commit: Optional[bool] = True) -> bool:
        """
        Deletes a device from the database.

        Args:
            db (Session): The database session.
            dev_id (int): The unique ID of the device to delete.
            commit (bool, optional): Whether to commit the transaction after deleting the device.

        Raises:
            HTTPException: If the device with the given ID does not exist.
        """
        logger.info(f"Attempting to delete device with ID: {dev_id}")

        device = cls.get_dev_by_id(db, dev_id)
        db.delete(device)
        if commit:
            try:
                db.commit()
                logger.info(f"Device with ID {dev_id} deleted successfully.")
            except Exception as e:
                logger.error(
                    f"Error while deleting device with ID {dev_id}: {e}")
                db.rollback()
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail=f"An internal error occurred while deleting device")
        return True


class DeviceNote(Base):
    __tablename__ = "device_note"
    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey(
        "device.id", ondelete="CASCADE", onupdate="CASCADE"), index=True)
    note: Mapped[str]
    timestamp: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    device = relationship("Device", back_populates="notes")

    @classmethod
    def get_dev_notes(cls,
                      db: Session,
                      dev_id: Optional[int]) -> List["DeviceNote"]:
        """
        Retrieves all notes associated with a specified device (if given).

        Args:
            db (Session): The database session.
            device_id (int, optional): The ID of the device to filter by.

        Returns:
            List[DeviceNote]: A list of DeviceNote objects.

        Raises:
            HTTPException: If no notes match the criteria.
        """
        logger.info("Attempting to retrieve device notes.")
        logger.debug(f"Filtering notes by device ID: {dev_id}")

        notes = db.query(DeviceNote)
        if dev_id:
            notes = notes.filter(DeviceNote.device_id == dev_id)
        notes = notes.all()
        if not notes:
            logger.warning(f"No device notes found with device ID: '{dev_id}'"
                           if dev_id else "No device notes found.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="No device notes that match given criteria found")

        logger.debug(f"Retrieved {len(notes)} notes for device ID: {dev_id}")
        return notes

    @classmethod
    def get_device_note_id(cls,
                           db: Session,
                           note_id: int) -> "DeviceNote":
        """
        Retrieves a specific note by its ID.

        Args:
            db (Session): The database session.
            note_id (int): The ID of the note to retrieve.

        Returns:
            DeviceNote: The DeviceNote object with the specified ID.

        Raises:
            HTTPException: If no note with the given ID exists.
        """
        logger.info(f"Attempting to retrieve note with ID: {note_id}")

        note = db.query(DeviceNote).filter(DeviceNote.id == note_id).first()
        if not note:
            logger.warning(f"Note with ID {note_id} not found.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"No device notes with id {note_id} found")

        logger.debug(f"Retrieved note: {note}")
        return note

    @classmethod
    def create_dev_note(cls,
                        db: Session,
                        note_data: schemas.DeviceNote,
                        commit: Optional[bool] = True) -> "DeviceNote":
        """
        Creates a new note for a device.

        Args:
            db (Session): The database session.
            note_data (schemas.DeviceNote): The data for creating the note.
            commit (bool, optional): Whether to commit the transaction after adding the note.

        Returns:
            DeviceNote: The created DeviceNote object.
        """
        logger.info("Creating a new device note.")
        logger.debug(f"Note data provided: {note_data}")

        note_data_dict = note_data.model_dump()
        note_data_dict["timestamp"] = datetime.datetime.now()
        note = DeviceNote(**note_data_dict)
        db.add(note)
        if commit:
            try:
                db.commit()
                logger.info(
                    "Device note created and committed to the database.")
            except Exception as e:
                db.rollback()
                logger.error(
                    f"Error while creating device note': {e}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail=f"An internal error occurred while creating note")

        logger.debug(f"New device note added to the database: {note}")
        return note

    @classmethod
    def update_dev_note(cls,
                        db: Session,
                        note_id: int,
                        note_data: schemas.NoteUpdate,
                        commit: Optional[bool] = True) -> "DeviceNote":
        """
        Updates an existing device note or deletes it if no content is provided.

        Args:
            db (Session): The database session.
            note_id (int): The ID of the note to update.
            note_data (schemas.NoteUpdate): The new content of the note.
            commit (bool, optional): Whether to commit the transaction after updating.

        Returns:
            DeviceNote: The updated DeviceNote object.

        Raises:
            HTTPException: If no note with the given ID exists, or if the note is deleted.
        """
        logger.info(f"Attempting to update note with ID: {note_id}")

        note = db.query(DeviceNote).filter(DeviceNote.id == note_id).first()
        if not note:
            logger.warning(f"Note with id {note_id} not found for update")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Note with id {note_id} not found")
        if note_data.note is None:
            logger.info(
                f"Deleting note with ID: {note_id} as new content is None.")
            cls.delete_device_note(db, note_id)
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT, detail="Note deleted")

        logger.debug(f"Updating note content to: {note_data.note}")
        note.note = note_data.note
        note.timestamp = datetime.datetime.now()

        if commit:
            try:
                db.commit()
                logger.info(f"Note with ID {note_id} updated successfully.")
            except Exception as e:
                db.rollback()
                logger.error(
                    f"Error while updating note with ID {note_id}: {e}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail=f"An internal error occurred while updating the note")

        logger.debug(f"Updated note in the database: {note}")
        return note

    @classmethod
    def delete_dev_note(cls,
                        db: Session,
                        note_id: int,
                        commit: Optional[bool] = True) -> bool:
        """
        Deletes a device note by its ID.

        Args:
            db (Session): The database session.
            note_id (int): The ID of the note to delete.
            commit (bool, optional): Whether to commit the transaction after deleting the note. Default is `True`.

        Raises:
            HTTPException: If no note with the given ID exists.
        """
        logger.info(f"Attempting to delete note with ID: {note_id}")

        note = db.query(DeviceNote).filter(DeviceNote.id == note_id).first()
        if not note:
            logger.warning(f"Note with ID {note_id} not found for deletion.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Note with id: {note_id} not found")
        db.delete(note)
        if commit:
            try:
                db.commit()
                logger.info(f"Note with ID {note_id} deleted successfully.")
            except Exception as e:
                db.rollback()
                logger.error(
                    f"Error while deleting note with ID {note_id}: {e}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail=f"An internal error occurred while deleting the note")

        logger.debug(f"Deleted note with ID {note_id} from the database.")
        return True
