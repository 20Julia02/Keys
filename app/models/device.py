from sqlalchemy import Integer, and_, case, ForeignKey, String, UniqueConstraint, func, TIMESTAMP
from sqlalchemy.orm import Mapped, relationship, mapped_column, Session
from enum import Enum
import datetime
from fastapi import HTTPException, status
from app.models.base import Base
from app import schemas
from app.models.operation import UserSession, DeviceOperation
from app.models.user import User
from typing import Optional, List, Literal
from sqlalchemy import Enum as SAEnum
from app.config import logger
from app.models.base import get_enum_values


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
        Retrieves a list of rooms from the database. 

        If `room_number` is provided, only returns the room(s) with the matching number. 
        If no room matches the criteria, raises an HTTPException.

        Args:
            db (Session): The database session.
            room_number (Optional[str]): The room number to filter by (if provided).

        Returns:
            List[Room]: A list of Room objects that match the criteria.

        Raises:
            HTTPException: 
                - 404 Not Found: If no rooms are found in the database.
        """
        logger.info("Fetching rooms from the database")
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

        logger.debug(
            f"Retrieved {len(rooms)} rooms that match given criteria")
        return rooms

    @classmethod
    def get_room_id(cls,
                    db: Session,
                    room_id: int) -> "Room":
        """
        Retrieves a room by its unique ID.

        If the room with the given ID is not found, raises an HTTPException.

        Args:
            db (Session): The database session.
            room_id (int): The unique ID of the room.

        Returns:
            Room: The Room object with the specified ID.

        Raises:
            HTTPException: 
                - 404 Not Found: If no room with the given ID exists in the database.
        """
        logger.info(f"Retrieving room by ID: {room_id}")

        room = db.query(Room).filter(Room.id == room_id).first()
        if not room:
            logger.warning(f"Room with ID {room_id} not found.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Room not found")
        logger.debug(f"Room retrieved: {room}")
        return room

    @classmethod
    def create_room(cls,
                    db: Session,
                    room_data: schemas.Room,
                    commit: Optional[bool] = True) -> "Room":
        """
        Creates a new room in the database.

        If a room with the specified number already exists, raises an HTTPException. 
        By default, commits the transaction immediately.

        Args:
            db (Session): The database session.
            room_data (schemas.RoomCreate): Data required to create the new room.
            commit (bool, optional): Whether to commit the transaction immediately. Default is True.

        Returns:
            Room: The newly created Room object.

        Raises:
            HTTPException: 
                - 404 Not Found: If a room with the specified number already exists.
                - 500 Internal Server Error: If an internal error occurs during the commit.
        """
        logger.info("Creating a new room.")
        logger.debug(f"Room data: {room_data}")

        if db.query(Room).filter_by(number=room_data.number).first():
            logger.warning(
                f"Attempted to create room with duplicate number '{room_data.number}'.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Room with this number already exists"
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

        If the room with the specified ID is not found, raises an HTTPException. 
        If the updated number already exists for another room, raises an HTTPException.

        Args:
            db (Session): The database session.
            room_id (int): The ID of the room to update.
            room_data (schemas.RoomUpdate): Data for updating the room.
            commit (bool, optional): Whether to commit the transaction immediately. Default is True.

        Returns:
            Room: The updated Room object.

        Raises:
            HTTPException: 
                - 404 Not Found: If the room is not found.
                - 400 Bad Request: If a room with the new number already exists.
                - 500 Internal Server Error: If an internal error occurs during the commit.
        """
        logger.info(f"Updating room with ID: {room_id}")
        logger.debug(f"New room data: {room_data}")

        room = db.query(Room).filter(Room.id == room_id).first()
        if not room:
            logger.warning(f"Room with ID {room_id} not found for update.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Room not found")

        if room_data.number != room.number:
            if db.query(Room).filter(Room.number == room_data.number).first():
                logger.warning(
                    f"Attempted to update room with duplicate number '{room_data.number}'.")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Room with this number already exists."
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
                                    detail="An internal error occurred while updating room")
        logger.debug(f"Updated room in the database: {room}")
        return room

    @classmethod
    def delete_room(cls,
                    db: Session,
                    room_id: int,
                    commit: Optional[bool] = True) -> bool:
        """
        Deletes a room by its unique ID from the database.

        If the room with the specified ID does not exist, raises an HTTPException. 
        By default, commits the transaction immediately.

        Args:
            db (Session): The database session.
            room_id (int): The unique ID of the room to delete.
            commit (bool, optional): Whether to commit the transaction immediately. Default is True.

        Returns:
            bool: True if the room was successfully deleted.

        Raises:
            HTTPException: 
                - 404 Not Found: If the room with the given ID does not exist.
                - 500 Internal Server Error: If an internal error occurs during the commit.
        """
        logger.info(f"Deleting room with ID: {room_id}")

        room = db.query(Room).filter(Room.id == room_id).first()
        if not room:
            logger.warning(f"Room with ID {room_id} not found for deletion.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Room doesn't exist")
        db.delete(room)
        if commit:
            try:
                db.commit()
                logger.info(f"Room with ID {room_id} deleted successfully.")
            except Exception as e:
                db.rollback()
                logger.error(f"Error deleting room ID {room_id}: {e}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail="An internal error occurred while deleting room")
        logger.debug(f"Device removed from database")
        return True


class DeviceVersion(Enum):
    primary = "podstawowa"
    backup = "zapasowa"


class DeviceType(Enum):
    key = "klucz"
    microphone = "mikrofon"
    remote_controler = "pilot"


class Device(Base):
    __tablename__ = "device"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    dev_type: Mapped[DeviceType] = mapped_column(
        SAEnum(DeviceType, values_callable=get_enum_values))
    room_id: Mapped[int] = mapped_column(ForeignKey(
        "room.id", ondelete="RESTRICT", onupdate="RESTRICT"), index=True)
    dev_version: Mapped[DeviceVersion] = mapped_column(
        SAEnum(DeviceVersion, values_callable=get_enum_values))

    room = relationship("Room", back_populates="devices")
    notes = relationship(
        "DeviceNote", back_populates="device")
    device_operations = relationship(
        "DeviceOperation", back_populates="device")
    unapproved_operations = relationship(
        "UnapprovedOperation", back_populates="device")

    __table_args__ = (
        UniqueConstraint("dev_type",
                         "dev_version", "room_id", name="uix_type_version"),
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
        Retrieves detailed information for devices, including related data such as room number, ownership status, and notes.

        Filters can be applied based on device type, version, and room number. Raises an HTTPException if no devices match the criteria.

        Args:
            db (Session): The database session.
            dev_type (Optional[str]): The type of device to filter by (e.g., 'klucz', 'mikrofon', 'pilot').
            dev_version (Optional[str]): The version of the device to filter by (e.g., 'podstawowa', 'zapasowa').
            room_number (Optional[str]): The room number to filter by.

        Returns:
            List[dict]: A list of dictionaries containing selected fields from Device, Room, and related tables.

        Raises:
            HTTPException: 
                - 404 Not Found: If no devices match the specified criteria.
        """
        logger.info("Retrieving devices with detailed information")
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
                    (DeviceOperation.operation_type ==
                     "pobranie", DeviceOperation.timestamp),
                    else_=None
                ).label("issue_time"),
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
                cls.id, Room.number, DeviceOperation.operation_type
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
            Device.id, Room.number, DeviceOperation.operation_type, User.name, User.surname, DeviceOperation.timestamp
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
            logger.warning("No devices found matching the specified criteria")
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
            HTTPException: 
            - 404 Not Found: If no device with the given ID exists.
        """
        logger.info(f"Attempting to retrieve device with ID: {dev_id}")
        device = db.query(cls).filter(cls.id == dev_id).first()
        if not device:
            logger.warning(f"Device with ID {dev_id} not found")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Device not found")
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
            HTTPException: 
            - 404 Not Found: If no device with the given code exists.
        """
        logger.info(f"Attempting to retrieve device with code: {dev_code}")

        device = db.query(cls).filter(cls.code == dev_code).first()
        if not device:
            logger.warning(f"Device with code {dev_code} not found.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Device not found")

        logger.debug(f"Device retrieved: {device}")
        return device

    @classmethod
    def create_dev(cls,
                   db: Session,
                   device_data: schemas.DeviceCreate,
                   commit: Optional[bool] = True) -> "Device":
        """
        Creates a new device in the database.

        Adds the device based on the provided data. Commits the transaction by default unless specified otherwise.

        Args:
            db (Session): The database session.
            device_data (schemas.DeviceCreate): The data required to create the new device.
            commit (bool, optional): Whether to commit the transaction immediately. Default is True.

        Returns:
            Device: The newly created Device object.

        Raises:
            HTTPException: 
            - 500 Internal Server Error: If an error occurs during the commit.
        """  
        logger.info("Creating a new device")
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
                                    detail="An internal error occurred while creating device")

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

        Modifies the device's attributes based on the provided data. Commits the transaction by default unless specified otherwise.

        Args:
            db (Session): The database session.
            dev_id (int): The unique ID of the device to update.
            device_data (schemas.DeviceUpdate): The data for updating the device.
            commit (bool, optional): Whether to commit the transaction immediately. Default is True.

        Returns:
            Device: The updated Device object.

        Raises:
            HTTPException: 
                - 404 Not Found: If no device with the given ID exists.
                - 500 Internal Server Error: If an error occurs during the commit.
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
                                    detail="An internal error occurred while updating device")

        return device

    @classmethod
    def delete_dev(cls,
                   db: Session,
                   dev_id: int,
                   commit: Optional[bool] = True) -> bool:
        """
        Deletes a device by its unique ID from the database. Commits the transaction by default unless specified otherwise.

        Args:
            db (Session): The database session.
            dev_id (int): The unique ID of the device to delete.
            commit (bool, optional): Whether to commit the transaction immediately. Default is True.

        Returns:
            bool: True if the device was successfully deleted.

        Raises:
            HTTPException: 
                - 404 Not Found: If the device with the given ID does not exist.
                - 500 Internal Server Error: If an error occurs during the commit.
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
                                    detail="An internal error occurred while deleting device")
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
        Retrieves all notes associated with a specified device.

        If a device ID is provided, only notes for that device are returned. 
        Raises an HTTPException if no notes match the criteria.

        Args:
            db (Session): The database session.
            dev_id (Optional[int]): The ID of the device to filter by (if provided).

        Returns:
            List[DeviceNote]: A list of DeviceNote objects that match the criteria.

        Raises:
            HTTPException: 
                - 404 Not Found: If no device notes match the criteria.
        """
        logger.info("Attempting to retrieve device notes.")
        logger.debug(f"Filtering notes by device ID: {dev_id}")

        notes = db.query(DeviceNote)
        if dev_id:
            notes = notes.filter(DeviceNote.device_id == dev_id)
        notes = notes.all()
        if not notes:
            logger.warning(f"No device notes found")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="No device notes that match given criteria found")

        logger.debug(
            f"Retrieved {len(notes)} device notes that match given criteria")
        return notes

    @classmethod
    def get_device_note_id(cls,
                           db: Session,
                           note_id: int) -> "DeviceNote":
        """
        Retrieves a specific note by its unique ID.

        Args:
            db (Session): The database session.
            note_id (int): The ID of the note to retrieve.

        Returns:
            DeviceNote: The DeviceNote object with the specified ID.

        Raises:
            HTTPException: 
                - 404 Not Found: If no device note with the given ID exists.
        """
        logger.info(f"Attempting to retrieve note with ID: {note_id}")

        note = db.query(DeviceNote).filter(DeviceNote.id == note_id).first()
        if not note:
            logger.warning(f"Note with ID {note_id} not found.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="No device note found")

        logger.debug(f"Retrieved note: {note}")
        return note

    @classmethod
    def create_dev_note(cls,
                        db: Session,
                        note_data: schemas.DeviceNote,
                        commit: Optional[bool] = True) -> "DeviceNote":
        """
        Creates a new note for a specified device.

        Adds the note based on the provided data. Commits the transaction by default unless specified otherwise.

        Args:
            db (Session): The database session.
            note_data (schemas.DeviceNote): The data required to create the new note.
            commit (bool, optional): Whether to commit the transaction immediately. Default is True.

        Returns:
            DeviceNote: The newly created DeviceNote object.

        Raises:
            HTTPException: 
                - 500 Internal Server Error: If an error occurs during the commit.
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
                                    detail="An internal error occurred while creating note")

        return note

    @classmethod
    def update_dev_note(cls,
                        db: Session,
                        note_id: int,
                        note_data: schemas.NoteUpdate,
                        commit: Optional[bool] = True) -> "DeviceNote":
        """
        Updates an existing device note.

        If the new content is `None`, the note will be deleted. Commits the transaction by default unless specified otherwise.

        Args:
            db (Session): The database session.
            note_id (int): The ID of the note to update.
            note_data (schemas.NoteUpdate): The new content of the note.
            commit (bool, optional): Whether to commit the transaction immediately. Default is True.

        Returns:
            DeviceNote: The updated DeviceNote object.

        Raises:
            HTTPException: 
                - 404 Not Found: If the note with the given ID does not exist.
                - 204 No Content: If the note is deleted due to `None` content.
                - 500 Internal Server Error: If an error occurs during the commit.
        """
        logger.info(f"Attempting to update device note with ID: {note_id}")

        note = db.query(DeviceNote).filter(DeviceNote.id == note_id).first()
        if not note:
            logger.warning(f"Note with id {note_id} not found for update")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Note not found")
        if note_data.note is None:
            logger.info(
                f"Deleting device note with ID: {note_id} as new content is None.")
            cls.delete_device_note(db, note_id)
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT, detail="Note deleted")

        logger.debug(f"Updating device note content to: {note_data.note}")
        note.note = note_data.note
        note.timestamp = datetime.datetime.now()

        if commit:
            try:
                db.commit()
                logger.info(
                    f"Device note with ID {note_id} updated successfully.")
            except Exception as e:
                db.rollback()
                logger.error(
                    f"Error while updating device note with ID {note_id}: {e}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail="An internal error occurred while updating device note")
        return note

    @classmethod
    def delete_dev_note(cls,
                        db: Session,
                        note_id: int,
                        commit: Optional[bool] = True) -> bool:
        """
        Deletes a specific device note by its unique ID. 
        Commits the transaction by default unless specified otherwise.

        Args:
            db (Session): The database session.
            note_id (int): The ID of the note to delete.
            commit (bool, optional): Whether to commit the transaction immediately. Default is True.

        Returns:
            bool: True if the note was successfully deleted.

        Raises:
            HTTPException: 
                - 404 Not Found: If the note with the given ID does not exist.
                - 500 Internal Server Error: If an error occurs during the commit.
        """
        logger.info(f"Attempting to delete device note with ID: {note_id}")

        note = db.query(DeviceNote).filter(DeviceNote.id == note_id).first()
        if not note:
            logger.warning(
                f"Device note with ID {note_id} not found for deletion")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Note not found")
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
                                    detail="An internal error occurred while deleting device note")
        return True
