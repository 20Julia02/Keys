import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
import app.models.device as mdevice
import datetime
import app.models.operation as moperation
from app.models.user import User, UnauthorizedUser, UserNote, UserRole
from app.models.permission import Permission, TokenBlacklist
from app import schemas
from app.services.securityService import PasswordService, TokenService, AuthorizationService
from jose import JWTError
from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

# device

# get_rooms

def test_get_rooms_no_rooms():
    db = MagicMock()
    db.query.return_value.all.return_value = []

    with pytest.raises(HTTPException) as excinfo:
        mdevice.Room.get_rooms(db)
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "No rooms found"


def test_get_rooms_with_rooms():
    db = MagicMock()
    mock_room = mdevice.Room(id=1, number="101")
    db.query.return_value.all.return_value = [mock_room]

    rooms = mdevice.Room.get_rooms(db)
    assert len(rooms) == 1
    assert rooms[0].number == "101"


def test_get_rooms_with_specific_number():
    db = MagicMock()
    mock_room = mdevice.Room(id=1, number="101")
    db.query.return_value.filter.return_value.all.return_value = [mock_room]

    rooms = mdevice.Room.get_rooms(db, room_number="101")
    assert len(rooms) == 1
    assert rooms[0].number == "101"

# get_room_id

def test_get_room_id_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as excinfo:
        mdevice.Room.get_room_id(db, room_id=-1)
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Room not found"


def test_get_room_id_found():
    db = MagicMock()
    mock_room = mdevice.Room(id=1, number="101")
    db.query.return_value.filter.return_value.first.return_value = mock_room

    room = mdevice.Room.get_room_id(db, room_id=1)
    assert room.id == 1
    assert room.number == "101"

# create_room


def test_create_room_success():
    db = MagicMock(spec=Session)
    db.query.return_value.filter_by.return_value.first.return_value = None
    mock_room_data = schemas.Room(number="101")
    db.commit.return_value = None

    room = mdevice.Room.create_room(db, mock_room_data)
    assert room.number == "101"
    db.add.assert_called_once()
    db.commit.assert_called_once()

def test_create_room_duplicate_number():
    db = MagicMock(spec=Session)
    mock_existing_room = MagicMock()
    db.query.return_value.filter_by.return_value.first.return_value = mock_existing_room
    mock_room_data = schemas.Room(number="101")

    with pytest.raises(HTTPException) as excinfo:
        mdevice.Room.create_room(db, mock_room_data)
    assert excinfo.value.status_code == 400
    assert excinfo.value.detail == "Room with this number already exists"

def test_create_room_commit_error():
    db = MagicMock(spec=Session)
    db.query.return_value.filter_by.return_value.first.return_value = None
    db.commit.side_effect = Exception("Commit error")
    mock_room_data = schemas.Room(number="101")

    with pytest.raises(HTTPException) as excinfo:
        mdevice.Room.create_room(db, mock_room_data)
    assert excinfo.value.status_code == 500
    assert excinfo.value.detail == "An internal error occurred while creating room."
    db.rollback.assert_called_once()

# update_room

def test_update_room_success():
    db = MagicMock(spec=Session)
    mock_existing_room = MagicMock(number="100")
    db.query.return_value.filter.return_value.first.side_effect = [mock_existing_room, None]
    mock_room_data = schemas.Room(number="101")

    room = mdevice.Room.update_room(db, room_id=1, room_data=mock_room_data)
    assert room.number == "101"
    db.commit.assert_called_once()

def test_update_room_not_found():
    db = MagicMock(spec=Session)
    db.query.return_value.filter.return_value.first.return_value = None
    mock_room_data = schemas.Room(number="101")

    with pytest.raises(HTTPException) as excinfo:
        mdevice.Room.update_room(db, room_id=-1, room_data=mock_room_data)
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Room not found"

def test_update_room_duplicate_number():
    db = MagicMock(spec=Session)
    mock_existing_room = MagicMock(number="100")
    mock_duplicate_room = MagicMock()
    db.query.return_value.filter.return_value.first.side_effect = [mock_existing_room, mock_duplicate_room]
    mock_room_data = schemas.Room(number="101")

    with pytest.raises(HTTPException) as excinfo:
        mdevice.Room.update_room(db, room_id=1, room_data=mock_room_data)
    assert excinfo.value.status_code == 400
    assert excinfo.value.detail == "Room with this number already exists."

def test_update_room_commit_error():
    db = MagicMock(spec=Session)
    mock_existing_room = MagicMock(number="100")
    db.query.return_value.filter.return_value.first.side_effect = [mock_existing_room, None]
    db.commit.side_effect = Exception("Commit error")
    mock_room_data = schemas.Room(number="101")

    with pytest.raises(HTTPException) as excinfo:
        mdevice.Room.update_room(db, room_id=1, room_data=mock_room_data)
    assert excinfo.value.status_code == 500
    assert excinfo.value.detail == "An internal error occurred while updating room"
    db.rollback.assert_called_once()

# delete_room

def test_delete_room_success():
    db = MagicMock(spec=Session)
    mock_existing_room = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = mock_existing_room
    db.commit.return_value = None

    result = mdevice.Room.delete_room(db, room_id=1)
    assert result is True
    db.delete.assert_called_once_with(mock_existing_room)
    db.commit.assert_called_once()

def test_delete_room_not_found():
    db = MagicMock(spec=Session)
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as excinfo:
        mdevice.Room.delete_room(db, room_id=-1)
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Room doesn't exist"

def test_delete_room_commit_error():
    db = MagicMock(spec=Session)
    mock_existing_room = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = mock_existing_room
    db.commit.side_effect = Exception("Commit error")

    with pytest.raises(HTTPException) as excinfo:
        mdevice.Room.delete_room(db, room_id=1)
    assert excinfo.value.status_code == 500
    assert excinfo.value.detail == "An internal error occurred while deleting room"
    db.rollback.assert_called_once()

# get_dev_with_details

def test_get_device_with_details_no_devices():
    db = MagicMock()

    db.query.return_value.all.return_value = []

    with pytest.raises(HTTPException) as excinfo:
        mdevice.Device.get_dev_with_details(db)

    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "No devices found matching criteria"


def test_get_device_with_details_with_criteria():
    db = MagicMock()

    mock_device = MagicMock(code="device_key_101",
                            dev_type="klucz", dev_version="podstawowa")

    query_mock = db.query.return_value
    query_mock.join.return_value = query_mock
    query_mock.outerjoin.return_value = query_mock
    query_mock.filter.return_value = query_mock
    query_mock.group_by.return_value = query_mock
    query_mock.order_by.return_value = query_mock
    query_mock.all.return_value = [mock_device]

    devices = mdevice.Device.get_dev_with_details(db, dev_type="klucz")

    assert len(devices) > 0
    assert "device_key_101" in [d.code for d in devices]

# get_dev_by_id

def test_get_by_id_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as excinfo:
        mdevice.Device.get_dev_by_id(db, dev_id=-1)
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Device not found"


def test_get_by_id_found():
    db = MagicMock()
    mock_device = MagicMock(id=1, code="device_key_101")
    db.query.return_value.filter.return_value.first.return_value = mock_device

    found_device = mdevice.Device.get_dev_by_id(db, dev_id=1)
    assert found_device.id == 1
    assert found_device.code == "device_key_101"

# get_dev_by_code

def test_get_by_code_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as excinfo:
        mdevice.Device.get_dev_by_code(db, dev_code="InvalidCode")
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Device not found"


def test_get_by_code_found():
    db = MagicMock()
    mock_device = MagicMock(code="device_key_101")
    db.query.return_value.filter.return_value.first.return_value = mock_device

    found_device = mdevice.Device.get_dev_by_code(
        db, dev_code="device_key_101")
    assert found_device.code == "device_key_101"

# create_dev

def test_create_dev_success():
    db = MagicMock(spec=Session)
    db.commit.return_value = None
    mock_device_data = schemas.DeviceCreate(code="DEF456", dev_type="klucz", dev_version="podstawowa", room_id=1)

    device = mdevice.Device.create_dev(db, mock_device_data)
    db.add.assert_called_once()
    db.commit.assert_called_once()
    assert device.code == "DEF456"

def test_create_dev_commit_error():
    db = MagicMock(spec=Session)
    db.commit.side_effect = Exception("Commit error")
    mock_device_data = schemas.DeviceCreate(code="DEF456", dev_type="klucz", dev_version="podstawowa", room_id=1)

    with pytest.raises(HTTPException) as excinfo:
        mdevice.Device.create_dev(db, mock_device_data)
    assert excinfo.value.status_code == 500
    assert excinfo.value.detail == "An internal error occurred while creating device"
    db.rollback.assert_called_once()

# update_dev

def test_update_dev_success():
    db = MagicMock(spec=Session)
    mock_device = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = mock_device
    mock_device_data = schemas.DeviceCreate(code="NEW123", dev_version="podstawowa", dev_type="klucz", room_id=1)

    updated_device = mdevice.Device.update_dev(db, dev_id=1, device_data=mock_device_data)
    db.commit.assert_called_once()
    assert updated_device.code == "NEW123"

def test_update_dev_not_found():
    db = MagicMock(spec=Session)
    db.query.return_value.filter.return_value.first.return_value = None
    mock_device_data = schemas.DeviceCreate(code="NEW123", dev_version="podstawowa", dev_type="klucz", room_id=1)

    with pytest.raises(HTTPException) as excinfo:
        mdevice.Device.update_dev(db, dev_id=-1, device_data=mock_device_data)
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Device not found"

def test_update_dev_commit_error():
    db = MagicMock(spec=Session)
    mock_device = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = mock_device
    db.commit.side_effect = Exception("Commit error")
    mock_device_data = schemas.DeviceCreate(code="NEW123", dev_version="podstawowa", dev_type="klucz", room_id=1)

    with pytest.raises(HTTPException) as excinfo:
        mdevice.Device.update_dev(db, dev_id=1, device_data=mock_device_data)
    assert excinfo.value.status_code == 500
    assert excinfo.value.detail == "An internal error occurred while updating device"
    db.rollback.assert_called_once()

# delete_dev

def test_delete_dev_success():
    db = MagicMock(spec=Session)
    mock_device = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = mock_device

    result = mdevice.Device.delete_dev(db, dev_id=1)
    db.delete.assert_called_once_with(mock_device)
    db.commit.assert_called_once()
    assert result is True

def test_delete_dev_not_found():
    db = MagicMock(spec=Session)
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as excinfo:
        mdevice.Device.delete_dev(db, dev_id=-1)
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Device not found"

def test_delete_dev_commit_error():
    db = MagicMock(spec=Session)
    mock_device = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = mock_device
    db.commit.side_effect = Exception("Commit error")

    with pytest.raises(HTTPException) as excinfo:
        mdevice.Device.delete_dev(db, dev_id=1)
    assert excinfo.value.status_code == 500
    assert excinfo.value.detail == "An internal error occurred while deleting device"
    db.rollback.assert_called_once()

# get_dev_notes

def test_get_dev_notes_no_notes():
    db = MagicMock(spec=Session)
    db.query.return_value.filter.return_value.all.return_value = []

    with pytest.raises(HTTPException) as excinfo:
        mdevice.DeviceNote.get_dev_notes(db, dev_id=1)
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "No device notes that match given criteria found"

def test_get_dev_notes_with_notes():
    db = MagicMock(spec=Session)
    mock_note = MagicMock(device_id=1, note="Test note")
    db.query.return_value.filter.return_value.all.return_value = [mock_note]

    notes = mdevice.DeviceNote.get_dev_notes(db, dev_id=1)
    assert len(notes) == 1
    assert notes[0].note == "Test note"

# get_device_note_id

def test_get_device_note_id_found():
    db = MagicMock(spec=Session)
    mock_note = MagicMock(id=1, note="Test note")
    db.query.return_value.filter.return_value.first.return_value = mock_note

    note = mdevice.DeviceNote.get_device_note_id(db, note_id=1)
    assert note.id == 1
    assert note.note == "Test note"

def test_get_device_note_id_not_found():
    db = MagicMock(spec=Session)
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as excinfo:
        mdevice.DeviceNote.get_device_note_id(db, note_id=-1)
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "No device note found"

# create_dev_note

def test_create_dev_note_success():
    db = MagicMock(spec=Session)
    db.commit.return_value = None
    mock_note_data = schemas.DeviceNote(device_id=1, note="New note")

    note = mdevice.DeviceNote.create_dev_note(db, mock_note_data)
    db.add.assert_called_once()
    db.commit.assert_called_once()
    assert note.note == "New note"

def test_create_dev_note_commit_error():
    db = MagicMock(spec=Session)
    db.commit.side_effect = Exception("Commit error")
    mock_note_data = schemas.DeviceNote(device_id=1, note="New note")

    with pytest.raises(HTTPException) as excinfo:
        mdevice.DeviceNote.create_dev_note(db, mock_note_data)
    assert excinfo.value.status_code == 500
    assert excinfo.value.detail == "An internal error occurred while creating note"
    db.rollback.assert_called_once()

# update_dev_note

def test_update_dev_note_success():
    db = MagicMock(spec=Session)
    mock_note = MagicMock(id=1, note="Old note")
    db.query.return_value.filter.return_value.first.return_value = mock_note
    mock_note_data = schemas.NoteUpdate(note="Updated note")

    updated_note = mdevice.DeviceNote.update_dev_note(db, note_id=1, note_data=mock_note_data)
    db.commit.assert_called_once()
    assert updated_note.note == "Updated note"

def test_update_dev_note_not_found():
    db = MagicMock(spec=Session)
    db.query.return_value.filter.return_value.first.return_value = None
    mock_note_data = schemas.NoteUpdate(note="Updated note")

    with pytest.raises(HTTPException) as excinfo:
        mdevice.DeviceNote.update_dev_note(db, note_id=-1, note_data=mock_note_data)
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Note not found"

def test_update_dev_note_delete_on_none_content():
    db = MagicMock(spec=Session)
    mock_note = MagicMock(id=1, note="Old note")
    db.query.return_value.filter.return_value.first.return_value = mock_note
    mock_note_data = schemas.NoteUpdate(note=None)

    with pytest.raises(HTTPException) as excinfo:
        mdevice.DeviceNote.update_dev_note(db, note_id=1, note_data=mock_note_data)
    assert excinfo.value.status_code == 204
    assert excinfo.value.detail == "Note deleted"

def test_update_dev_note_commit_error():
    db = MagicMock(spec=Session)
    mock_note = MagicMock(id=1, note="Old note")
    db.query.return_value.filter.return_value.first.return_value = mock_note
    db.commit.side_effect = Exception("Commit error")
    mock_note_data = schemas.NoteUpdate(note="Updated note")

    with pytest.raises(HTTPException) as excinfo:
        mdevice.DeviceNote.update_dev_note(db, note_id=1, note_data=mock_note_data)
    assert excinfo.value.status_code == 500
    assert excinfo.value.detail == "An internal error occurred while updating device note"
    db.rollback.assert_called_once()

# delete_dev_note

def test_delete_dev_note_success():
    db = MagicMock(spec=Session)
    mock_note = MagicMock(id=1)
    db.query.return_value.filter.return_value.first.return_value = mock_note

    result = mdevice.DeviceNote.delete_dev_note(db, note_id=1)
    db.delete.assert_called_once_with(mock_note)
    db.commit.assert_called_once()
    assert result is True

def test_delete_dev_note_not_found():
    db = MagicMock(spec=Session)
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as excinfo:
        mdevice.DeviceNote.delete_dev_note(db, note_id=-1)
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Note not found"

def test_delete_dev_note_commit_error():
    db = MagicMock(spec=Session)
    mock_note = MagicMock(id=1)
    db.query.return_value.filter.return_value.first.return_value = mock_note
    db.commit.side_effect = Exception("Commit error")

    with pytest.raises(HTTPException) as excinfo:
        mdevice.DeviceNote.delete_dev_note(db, note_id=1)
    assert excinfo.value.status_code == 500
    assert excinfo.value.detail == "An internal error occurred while deleting device note"
    db.rollback.assert_called_once()

# operation
# create_session

# create_session

def test_create_session_success():
    db = MagicMock()
    db.commit.return_value = None
    db.refresh.return_value = None

    session = moperation.UserSession.create_session(db, user_id=1, concierge_id=2, commit=True)
    assert session.user_id == 1
    assert session.concierge_id == 2
    assert session.status == "w trakcie"
    assert isinstance(session.start_time, datetime.datetime)
    db.add.assert_called_once_with(session)
    db.commit.assert_called_once()

def test_create_session_commit_error():
    db = MagicMock()
    db.commit.side_effect = SQLAlchemyError("Commit error")

    with pytest.raises(HTTPException) as excinfo:
        moperation.UserSession.create_session(db, user_id=1, concierge_id=2, commit=True)
    assert excinfo.value.status_code == 500
    assert excinfo.value.detail == "An internal error occurred while creating session"
    db.rollback.assert_called_once()

# end_session

def test_end_session_success():
    db = MagicMock()
    mock_session = MagicMock(status="w trakcie", end_time=None)
    db.query.return_value.filter_by.return_value.first.return_value = mock_session

    session = moperation.UserSession.end_session(db, session_id=1, reject=False, commit=True)
    assert session.status == "potwierdzona"
    assert isinstance(session.end_time, datetime.datetime)
    db.commit.assert_called_once()

def test_end_session_reject():
    db = MagicMock()
    mock_session = MagicMock(status="w trakcie", end_time=None)
    db.query.return_value.filter_by.return_value.first.return_value = mock_session

    session = moperation.UserSession.end_session(db, session_id=1, reject=True, commit=True)
    assert session.status == "odrzucona"
    assert isinstance(session.end_time, datetime.datetime)
    db.commit.assert_called_once()

def test_end_session_not_found():
    db = MagicMock()
    db.query.return_value.filter_by.return_value.first.return_value = None

    with pytest.raises(HTTPException) as excinfo:
        moperation.UserSession.end_session(db, session_id=-1, reject=False, commit=True)
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Session not found"

def test_end_session_already_ended():
    db = MagicMock()
    mock_session = MagicMock(status="potwierdzona", end_time=datetime.datetime.now())
    db.query.return_value.filter_by.return_value.first.return_value = mock_session

    with pytest.raises(HTTPException) as excinfo:
        moperation.UserSession.end_session(db, session_id=1, reject=False, commit=True)
    assert excinfo.value.status_code == 403
    assert excinfo.value.detail == "Session has been allready ended"

# get_session_id

def test_get_session_id_success():
    db = MagicMock()
    mock_session = MagicMock(id=1, status="w trakcie")
    db.query.return_value.filter.return_value.first.return_value = mock_session

    session = moperation.UserSession.get_session_id(db, session_id=1)
    assert session.id == 1
    assert session.status == "w trakcie"

def test_get_session_id_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as excinfo:
        moperation.UserSession.get_session_id(db, session_id=-1)
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Session doesn't exist"

# permission

# Test get_permissions

def test_get_permissions_no_permissions():
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

    with pytest.raises(HTTPException) as excinfo:
        Permission.get_permissions(db)
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "No permissions found that match given criteria"

def test_get_permissions_with_filters():
    db = MagicMock()

    current_date = datetime.date.today()
    current_time = datetime.datetime.now().time()

    mock_permission = MagicMock(
        user_id=1,
        room_id=1,
        date=current_date,
        start_time=datetime.time(9, 0),
        end_time=datetime.time(12, 0),
    )

    db.query.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = [
        mock_permission
    ]

    with patch("datetime.date") as mock_date, patch("datetime.datetime") as mock_datetime:
        mock_date.today.return_value = current_date
        mock_datetime.now.return_value = datetime.datetime.combine(current_date, current_time)

        permissions = Permission.get_permissions(db, user_id=1, room_id=1)

        assert len(permissions) == 1
        assert permissions[0].user_id == 1
        assert permissions[0].room_id == 1


def test_get_permissions_current_date_and_time():
    db: MagicMock = MagicMock()
    current_date = datetime.date.today()
    current_time = datetime.time(10, 0)

    mock_permission = MagicMock(
        date=current_date,
        start_time=datetime.time(9, 0),
        end_time=datetime.time(17, 0)
    )

    query_mock: MagicMock = db.query.return_value

    def side_effect_filter(*args: Any, **kwargs: Any) -> MagicMock:
        return query_mock

    query_mock.filter.side_effect = side_effect_filter
    query_mock.order_by.return_value.all.return_value = [mock_permission]

    with patch("datetime.date") as mock_date, patch("datetime.datetime") as mock_datetime:
        mock_date.today.return_value = current_date
        mock_datetime.now.return_value = datetime.datetime.combine(current_date, current_time)

        permissions = Permission.get_permissions(db, date=current_date, time=current_time)

        assert len(permissions) == 1, f"Expected 1 permission, got {len(permissions)}"
        assert permissions[0].date == current_date
        assert permissions[0].start_time <= current_time <= permissions[0].end_time

# Test check_if_permitted

def test_check_if_permitted_success():
    db = MagicMock()
    mock_permission = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = mock_permission

    result = Permission.check_if_permitted(db, user_id=1, room_id=1)
    assert result is True

def test_check_if_permitted_failure():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    result = Permission.check_if_permitted(db, user_id=1, room_id=1)
    assert result is False

# Test create_permission

def test_create_permission_success():
    db = MagicMock()
    db.commit.return_value = None
    mock_permission_data = MagicMock()
    mock_permission_data.model_dump = MagicMock(return_value={
        'user_id': 1,
        'room_id': 2,
        'date': datetime.date.today(),
        'start_time': datetime.time(9, 0),
        'end_time': datetime.time(17, 0),
    })

    permission = Permission.create_permission(db, mock_permission_data, commit=True)
    assert permission.user_id == 1
    assert permission.room_id == 2
    db.add.assert_called_once()
    db.commit.assert_called_once()

def test_create_permission_commit_error():
    db = MagicMock()
    db.commit.side_effect = SQLAlchemyError("Commit error")
    mock_permission_data = MagicMock()
    mock_permission_data.model_dump = MagicMock(return_value={
        'user_id': 1,
        'room_id': 2,
        'date': datetime.date.today(),
        'start_time': datetime.time(9, 0),
        'end_time': datetime.time(17, 0),
    })

    with pytest.raises(HTTPException) as excinfo:
        Permission.create_permission(db, mock_permission_data, commit=True)
    assert excinfo.value.status_code == 500
    assert excinfo.value.detail == "An internal error occurred while creating permission"
    db.rollback.assert_called_once()

# Test update_permission

def test_update_permission_success():
    db = MagicMock()
    mock_permission = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = mock_permission
    mock_permission_data = MagicMock(user_id=1, room_id=2, date=datetime.datetime.today(), start_time="9:00:00", end_time="17:00:00")

    permission = Permission.update_permission(db, permission_id=1, permission_data=mock_permission_data, commit=True)
    assert permission.user_id == 1
    assert permission.room_id == 2
    db.commit.assert_called_once()

def test_update_permission_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    mock_permission_data = MagicMock()

    with pytest.raises(HTTPException) as excinfo:
        Permission.update_permission(db, permission_id=-1, permission_data=mock_permission_data, commit=True)
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Permission doesn't exist"

# Test delete_permission

def test_delete_permission_success():
    db = MagicMock()
    mock_permission = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = mock_permission

    result = Permission.delete_permission(db, permission_id=1, commit=True)
    assert result is True
    db.delete.assert_called_once_with(mock_permission)
    db.commit.assert_called_once()

def test_delete_permission_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as excinfo:
        Permission.delete_permission(db, permission_id=-1, commit=True)
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Permission doesn't exist"

# Test get_active_permissions

def test_get_active_permissions_no_permissions():
    db = MagicMock()

    query_mock = db.query.return_value
    query_mock.join.return_value.filter.return_value.order_by.return_value.all.return_value = []

    with pytest.raises(HTTPException) as excinfo:
        Permission.get_active_permissions(db, user_id=1)

    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "No permissions found that match given criteria"

def test_get_active_permissions_success():
    db = MagicMock()

    mock_permission = MagicMock()

    query_mock = db.query.return_value
    query_mock.join.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_permission]

    permissions = Permission.get_active_permissions(db, user_id=1)

    assert len(permissions) == 1
    assert permissions[0] == mock_permission

# users

# Test get_all_users

def test_get_all_users_success():
    db = MagicMock()
    mock_users = [MagicMock(), MagicMock()]
    db.query.return_value.all.return_value = mock_users

    users = User.get_all_users(db)
    assert len(users) == 2
    assert users == mock_users


def test_get_all_users_no_users_found():
    db = MagicMock()
    db.query.return_value.all.return_value = []

    with pytest.raises(HTTPException) as excinfo:
        User.get_all_users(db)

    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "There is no user in the database"

# # Test get_user_id

def test_get_user_id_success():
    db = MagicMock()
    mock_user = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = mock_user

    user = User.get_user_id(db, user_id=1)
    assert user == mock_user

# create_user

def test_get_user_id_user_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as excinfo:
        User.get_user_id(db, user_id=1)

    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "User doesn't exist"

def test_create_user_success():
    db = MagicMock()
    mock_user_data = MagicMock(model_dump=MagicMock(return_value={
        "name": "John",
        "surname": "Doe",
        "email": "john.doe@example.com",
        "password": "hashed_password",
        "role": UserRole.employee,
        "card_code": "12345"
    }))

    with patch("app.services.securityService.PasswordService.hash_password", return_value="hashed_password"):
        user = User.create_user(db, mock_user_data)

    db.add.assert_called_once()
    db.commit.assert_called_once()
    assert user is not None


def test_create_user_commit_error():
    db = MagicMock()
    db.commit.side_effect = Exception("Commit failed")
    mock_user_data = MagicMock(model_dump=MagicMock(return_value={
        "name": "John",
        "surname": "Doe",
        "email": "john.doe@example.com",
        "password": "hashed_password",
        "role": UserRole.employee,
        "card_code": "12345"
    }))

    with patch("app.services.securityService.PasswordService.hash_password", return_value="hashed_password"):
        with pytest.raises(HTTPException) as excinfo:
            User.create_user(db, mock_user_data)

    db.rollback.assert_called_once()
    assert excinfo.value.status_code == 500
    assert excinfo.value.detail == "An internal error occurred while creating user"

# delete_user

def test_delete_user_success():
    db = MagicMock()
    mock_user = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = mock_user

    result = User.delete_user(db, user_id=1)
    db.delete.assert_called_once_with(mock_user)
    db.commit.assert_called_once()
    assert result is True


def test_delete_user_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as excinfo:
        User.delete_user(db, user_id=1)

    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "User doesn't exist"


def test_delete_user_commit_error():
    db = MagicMock()
    mock_user = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = mock_user
    db.commit.side_effect = Exception("Commit failed")

    with pytest.raises(HTTPException) as excinfo:
        User.delete_user(db, user_id=1)

    db.rollback.assert_called_once()
    assert excinfo.value.status_code == 500
    assert excinfo.value.detail == "An internal error occurred while deleting user"

# update_user

def test_update_user_success():
    db = MagicMock()
    mock_user = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = mock_user
    mock_user_data = MagicMock(model_dump=MagicMock(return_value={
        "name": "John",
        "surname": "Doe",
        "email": "john.doe@example.com",
        "password": "hashed_password",
        "role": UserRole.employee,
        "card_code": "12345"
    }))

    with patch("app.services.securityService.PasswordService.hash_password", return_value="hashed_password"):
        updated_user = User.update_user(db, user_id=1, user_data=mock_user_data)

    db.commit.assert_called_once()
    assert updated_user == mock_user


def test_update_user_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    mock_user_data = MagicMock()

    with pytest.raises(HTTPException) as excinfo:
        User.update_user(db, user_id=1, user_data=mock_user_data)

    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "User not found"


def test_update_user_commit_error():
    db = MagicMock()
    mock_user = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = mock_user
    db.commit.side_effect = Exception("Commit failed")
    mock_user_data = MagicMock(model_dump=MagicMock(return_value={
        "name": "John",
        "surname": "Doe",
        "email": "john.doe@example.com",
        "password": "hashed_password",
        "role": UserRole.employee,
        "card_code": "12345"
    }))

    with patch("app.services.securityService.PasswordService.hash_password", return_value="hashed_password"):
        with pytest.raises(HTTPException) as excinfo:
            User.update_user(db, user_id=1, user_data=mock_user_data)

    db.rollback.assert_called_once()
    assert excinfo.value.status_code == 500
    assert excinfo.value.detail == "An internal error occurred while updating user"

# Test create_or_get_unauthorized_user

def test_create_or_get_unauthorized_user_existing_user_match():
    db = MagicMock()

    mock_user = MagicMock()
    mock_user.name = "John"
    mock_user.surname = "Doe"
    mock_user.email = "john@example.com"

    db.query.return_value.filter_by.return_value.first.return_value = mock_user

    user, is_new = UnauthorizedUser.create_or_get_unauthorized_user(
        db, name="John", surname="Doe", email="john@example.com"
    )

    assert user == mock_user
    assert not is_new

def test_create_or_get_unauthorized_user_existing_user_mismatch():
    db = MagicMock()
    mock_user = MagicMock(name="Jane", surname="Smith", email="john@example.com")
    db.query.return_value.filter_by.return_value.first.return_value = mock_user

    with pytest.raises(HTTPException) as excinfo:
        UnauthorizedUser.create_or_get_unauthorized_user(
            db, name="John", surname="Doe", email="john@example.com"
        )

    assert excinfo.value.status_code == 409
    assert excinfo.value.detail == "User with this email already exists but with a different name or surname"

def test_create_or_get_unauthorized_user_new_user():
    db = MagicMock()
    db.query.return_value.filter_by.return_value.first.return_value = None

    user, is_new = UnauthorizedUser.create_or_get_unauthorized_user(
        db, name="John", surname="Doe", email="john@example.com"
    )

    db.add.assert_called_once()
    db.commit.assert_called_once()
    assert user.name == "John"
    assert user.surname == "Doe"
    assert user.email == "john@example.com"
    assert is_new

# Test get_all_unathorized_users

def test_get_all_unauthorized_users_success():
    db = MagicMock()
    mock_users = [MagicMock(), MagicMock()]
    db.query.return_value.all.return_value = mock_users

    users = UnauthorizedUser.get_all_unathorized_users(db)

    assert len(users) == 2
    assert users == mock_users

def test_get_all_unauthorized_users_no_users():
    db = MagicMock()
    db.query.return_value.all.return_value = []

    with pytest.raises(HTTPException) as excinfo:
        UnauthorizedUser.get_all_unathorized_users(db)

    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "There is no unauthorized user in database"

# Test get_unathorized_user

def test_get_unauthorized_user_success():
    db = MagicMock()
    mock_user = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = mock_user

    user = UnauthorizedUser.get_unathorized_user(db, user_id=1)

    assert user == mock_user

def test_get_unauthorized_user_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as excinfo:
        UnauthorizedUser.get_unathorized_user(db, user_id=1)

    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Unauthorized user doesn't exist"

# Test get_unathorized_user_email

def test_get_unauthorized_user_email_success():
    db = MagicMock()
    mock_user = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = mock_user

    user = UnauthorizedUser.get_unathorized_user_email(db, email="test@example.com")

    assert user == mock_user

def test_get_unauthorized_user_email_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as excinfo:
        UnauthorizedUser.get_unathorized_user_email(db, email="test@example.com")

    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Unauthorized user doesn't exist"

# Test update_unauthorized_user

def test_update_unauthorized_user_success():
    db = MagicMock()
    mock_user = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = mock_user
    mock_user_data = MagicMock(model_dump=MagicMock(return_value={
        "name": "John",
        "surname": "Doe",
        "email": "john@example.com"
    }))

    user = UnauthorizedUser.update_unauthorized_user(db, user_id=1, user_data=mock_user_data)

    db.commit.assert_called_once()
    assert user == mock_user

def test_update_unauthorized_user_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    mock_user_data = MagicMock()

    with pytest.raises(HTTPException) as excinfo:
        UnauthorizedUser.update_unauthorized_user(db, user_id=1, user_data=mock_user_data)

    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Unauthorized user not found"

def test_update_unauthorized_user_commit_error():
    db = MagicMock()
    mock_user = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = mock_user
    db.commit.side_effect = Exception("Commit failed")
    mock_user_data = MagicMock(model_dump=MagicMock(return_value={
        "name": "John",
        "surname": "Doe",
        "email": "john@example.com"
    }))

    with pytest.raises(HTTPException) as excinfo:
        UnauthorizedUser.update_unauthorized_user(db, user_id=1, user_data=mock_user_data)

    db.rollback.assert_called_once()
    assert excinfo.value.status_code == 500
    assert excinfo.value.detail == "An internal error occurred while updating unauthorized user"

# Test delete_unauthorized_user

def test_delete_unauthorized_user_success():
    db = MagicMock()
    mock_user = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = mock_user

    result = UnauthorizedUser.delete_unauthorized_user(db, user_id=1)

    db.delete.assert_called_once_with(mock_user)
    db.commit.assert_called_once()
    assert result is True

def test_delete_unauthorized_user_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as excinfo:
        UnauthorizedUser.delete_unauthorized_user(db, user_id=1)

    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Unauthorized user doesn't exist"

def test_delete_unauthorized_user_commit_error():
    db = MagicMock()
    mock_user = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = mock_user
    db.commit.side_effect = Exception("Commit failed")

    with pytest.raises(HTTPException) as excinfo:
        UnauthorizedUser.delete_unauthorized_user(db, user_id=1)

    db.rollback.assert_called_once()
    assert excinfo.value.status_code == 500
    assert excinfo.value.detail == "An internal error occurred while deleting unauthorized user"


# Test get_user_notes_filter
def test_get_user_notes_filter_with_user_id():
    db = MagicMock()
    mock_note = MagicMock(user_id=1, note="Test note", timestamp=datetime.datetime.now())
    db.query.return_value.filter.return_value.all.return_value = [mock_note]

    result = UserNote.get_user_notes_filter(db, user_id=1)

    assert len(result) == 1
    assert result[0].user_id == 1
    assert result[0].note == "Test note"


def test_get_user_notes_filter_without_user_id():
    db = MagicMock()
    mock_note1 = MagicMock(user_id=1, note="Note 1", timestamp=datetime.datetime.now())
    mock_note2 = MagicMock(user_id=2, note="Note 2", timestamp=datetime.datetime.now())
    db.query.return_value.all.return_value = [mock_note1, mock_note2]

    result = UserNote.get_user_notes_filter(db)

    assert len(result) == 2


def test_get_user_notes_filter_no_notes_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.all.return_value = []

    with pytest.raises(HTTPException) as excinfo:
        UserNote.get_user_notes_filter(db, user_id=1)

    assert excinfo.value.status_code == 404
    assert "No user notes found" in excinfo.value.detail


# Test get_user_note_id
def test_get_user_note_id_success():
    db = MagicMock()
    mock_note = MagicMock(id=1, note="Test note", timestamp=datetime.datetime.now())
    db.query.return_value.filter.return_value.first.return_value = mock_note

    result = UserNote.get_user_note_id(db, note_id=1)

    assert result == mock_note
    assert result.id == 1
    assert result.note == "Test note"


def test_get_user_note_id_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as excinfo:
        UserNote.get_user_note_id(db, note_id=1)

    assert excinfo.value.status_code == 404
    assert "There is no user note with this id" in excinfo.value.detail


# Test create_user_note
def test_create_user_note_success():
    db = MagicMock()
    note_data = schemas.UserNoteCreate(user_id=1, note="New note")
    MagicMock(**note_data.model_dump(), timestamp=datetime.datetime.now())
    db.add = MagicMock()

    result = UserNote.create_user_note(db, note_data)

    db.add.assert_called_once()
    assert result.user_id == note_data.user_id
    assert result.note == note_data.note


def test_create_user_note_commit_error():
    db = MagicMock()
    note_data = schemas.UserNoteCreate(user_id=1, note="New note")
    db.commit.side_effect = Exception("Commit error")

    with pytest.raises(HTTPException) as excinfo:
        UserNote.create_user_note(db, note_data)

    assert excinfo.value.status_code == 500
    assert "An internal error occurred while creating user note" in excinfo.value.detail
    db.rollback.assert_called_once()


# Test update_user_note
def test_update_user_note_success():
    db = MagicMock()
    mock_note = MagicMock(id=1, note="Old note", timestamp=datetime.datetime.now())
    db.query.return_value.filter.return_value.first.return_value = mock_note
    note_data = schemas.NoteUpdate(note="Updated note")

    result = UserNote.update_user_note(db, note_id=1, note_data=note_data)

    assert result.note == "Updated note"
    db.commit.assert_called_once()


def test_update_user_note_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    note_data = schemas.NoteUpdate(note="Updated note")

    with pytest.raises(HTTPException) as excinfo:
        UserNote.update_user_note(db, note_id=1, note_data=note_data)

    assert excinfo.value.status_code == 404
    assert "Note not found" in excinfo.value.detail


def test_update_user_note_deletion():
    db = MagicMock()
    mock_note = MagicMock(id=1, note="Old note", timestamp=datetime.datetime.now())
    db.query.return_value.filter.return_value.first.return_value = mock_note
    note_data = schemas.NoteUpdate(note=None)

    with pytest.raises(HTTPException) as excinfo:
        UserNote.update_user_note(db, note_id=1, note_data=note_data)

    assert excinfo.value.status_code == 204
    assert "Note deleted" in excinfo.value.detail
    db.delete.assert_called_once_with(mock_note)


# Test delete_user_note
def test_delete_user_note_success():
    db = MagicMock()
    mock_note = MagicMock(id=1, note="Test note")
    db.query.return_value.filter.return_value.first.return_value = mock_note

    result = UserNote.delete_user_note(db, note_id=1)

    assert result is True
    db.delete.assert_called_once_with(mock_note)
    db.commit.assert_called_once()


def test_delete_user_note_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as excinfo:
        UserNote.delete_user_note(db, note_id=1)

    assert excinfo.value.status_code == 404
    assert "Note doesn't exist" in excinfo.value.detail

# Test hash_password

def test_hash_password():
    password_service = PasswordService()
    password = "supersecret"
    hashed_password = password_service.hash_password(password)
    assert hashed_password != password
    assert password_service.verify_hashed(password, hashed_password)

# Test verify_hashed

def test_verify_hashed_password_match():
    password_service = PasswordService()
    password = "mypassword"
    hashed_password = password_service.hash_password(password)
    assert password_service.verify_hashed(password, hashed_password)


def test_verify_hashed_password_no_match():
    password_service = PasswordService()
    password = "mypassword"
    hashed_password = password_service.hash_password(password)
    assert not password_service.verify_hashed("wrongpassword", hashed_password)

# Test create_token

def test_create_token():
    db = MagicMock()
    token_service = TokenService(db)
    data: dict[Any, Any] = {"user_id": 1, "user_role": "concierge"}
    token = token_service.create_token(data, "access")
    assert token is not None


def test_create_token_with_special_characters():
    db = MagicMock()
    token_service = TokenService(db)
    data: dict[str, Any] = {"user_id": 1,
                            "user_role": "admin", "extra_info": "@#$%^&*()!"}
    token = token_service.create_token(data, "access")
    assert token is not None

# Test verify_concierge_token

@patch("jose.jwt.decode")
def test_verify_concierge_token_valid(mock_jwt_decode: Any):
    mock_jwt_decode.return_value = {"user_id": 1, "user_role": "portier"}
    db = MagicMock()
    token_service = TokenService(db)
    token = "sometoken"
    token_data = token_service.verify_concierge_token(token)
    assert token_data.id == 1
    assert token_data.role == "portier"


@patch("jose.jwt.decode", side_effect=JWTError)
def test_verify_concierge_token_invalid(mock_jwt_decode: Any):
    db = MagicMock()
    token_service = TokenService(db)
    token = "invalidtoken"

    with pytest.raises(HTTPException) as excinfo:
        token_service.verify_concierge_token(token)
    assert excinfo.value.status_code == 401
    assert excinfo.value.detail == "Failed to verify token"

# Test is_token_blacklisted

def test_is_token_blacklisted():
    db = MagicMock()
    db.query.return_value.filter_by.return_value.first.return_value = None
    token_service = TokenService(db)
    assert not token_service.is_token_blacklisted("sometoken")


def test_is_token_blacklisted_true():
    db = MagicMock()
    db.query.return_value.filter_by.return_value.first.return_value = TokenBlacklist(
        token="blacklisted_token")
    token_service = TokenService(db)

    assert token_service.is_token_blacklisted("blacklisted_token") is True
# TODO add_token_to_blacklist, generate_tokens, get_current_concierge_token, authenticate_user_card

# Test entitled_or_error

def test_entitled_or_error_user_has_role():
    db = MagicMock()
    auth_service = AuthorizationService(db)
    user = User(role=UserRole.concierge)
    auth_service.entitled_or_error(UserRole.concierge, user)


def test_entitled_or_error_user_no_role():
    db = MagicMock()
    auth_service = AuthorizationService(db)
    user = User(role=UserRole.employee)

    with pytest.raises(HTTPException) as excinfo:
        auth_service.entitled_or_error(UserRole.admin, user)
    assert excinfo.value.status_code == 403
    assert excinfo.value.detail == "You cannot perform this operation without the appropriate role"

# Test get_current_concierge

@patch.object(TokenService, "is_token_blacklisted", return_value=True)
def test_get_current_concierge_blacklisted_token(mock_is_blacklisted: Any):
    db = MagicMock()
    auth_service = AuthorizationService(db)
    token = "blacklisted_token"

    with pytest.raises(HTTPException) as excinfo:
        auth_service.get_current_concierge(token)
    assert excinfo.value.status_code == 403
    assert excinfo.value.detail == "Concierge is logged out"


@patch.object(TokenService, "is_token_blacklisted", return_value=False)
@patch.object(TokenService, "verify_concierge_token")
def test_get_current_concierge_user_not_found(mock_verify_token: Any, mock_is_token_blacklisted: Any):
    mock_verify_token.return_value = schemas.TokenData(id=1, role="portier")
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    auth_service = AuthorizationService(db)
    token = "valid_token"

    with pytest.raises(HTTPException) as excinfo:
        auth_service.get_current_concierge(token)
    assert excinfo.value.status_code == 401
    assert excinfo.value.detail == "Could not validate credentials"

# Test authenticate_user_login

@patch.object(PasswordService, "verify_hashed", return_value=True)
def test_authenticate_user_login_success(mock_verify_hashed: Any):
    db = MagicMock()
    auth_service = AuthorizationService(db)
    user = User(email="test@example.com",
                password="hashedpassword", role=UserRole.concierge)
    db.query.return_value.filter_by.return_value.first.return_value = user

    authenticated_user = auth_service.authenticate_user_login(
        "test@example.com", "mypassword", "concierge")
    assert authenticated_user == user


@patch.object(PasswordService, "verify_hashed", return_value=False)
def test_authenticate_user_login_failure(mock_verify_hashed: Any):
    db = MagicMock()
    auth_service = AuthorizationService(db)
    db.query.return_value.filter_by.return_value.first.return_value = None

    with pytest.raises(HTTPException) as excinfo:
        auth_service.authenticate_user_login(
            "test@example.com", "wrongpassword", "concierge")
    assert excinfo.value.status_code == 403
    assert excinfo.value.detail == "Invalid credentials"
