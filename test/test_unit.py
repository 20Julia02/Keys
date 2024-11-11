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


def test_get_rooms_no_rooms():
    db = MagicMock()
    db.query.return_value.all.return_value = []

    with pytest.raises(HTTPException) as excinfo:
        mdevice.Room.get_rooms(db)
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "No rooms found matching the specified number"


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


def test_get_room_id_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as excinfo:
        mdevice.Room.get_room_id(db, room_id=-1)
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Room with id: -1 doesn't exist"


def test_get_room_id_found():
    db = MagicMock()
    mock_room = mdevice.Room(id=1, number="101")
    db.query.return_value.filter.return_value.first.return_value = mock_room

    room = mdevice.Room.get_room_id(db, room_id=1)
    assert room.id == 1
    assert room.number == "101"


def test_get_device_with_details_no_devices():
    db = MagicMock()

    db.query.return_value.all.return_value = []

    with pytest.raises(HTTPException) as excinfo:
        mdevice.Device.get_device_with_details(db)

    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "There are no devices that match the given criteria in the database"


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

    devices = mdevice.Device.get_device_with_details(db, dev_type="klucz")

    assert len(devices) > 0
    assert "device_key_101" in [d.code for d in devices]


def test_get_device_with_invalid_type():
    db = MagicMock()

    with pytest.raises(HTTPException) as excinfo:
        mdevice.Device.get_device_with_details(db, dev_type="InvalidType")
    assert excinfo.value.status_code == 400
    assert excinfo.value.detail == "Invalid device type: InvalidType"


def test_get_device_with_invalid_version():
    db = MagicMock()

    with pytest.raises(HTTPException) as excinfo:
        mdevice.Device.get_device_with_details(
            db, dev_version="InvalidVersion")
    assert excinfo.value.status_code == 400
    assert excinfo.value.detail == "Invalid device version: InvalidVersion"


def test_get_by_id_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as excinfo:
        mdevice.Device.get_by_id(db, dev_id=-1)
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Device with id: -1 doesn't exist"


def test_get_by_id_found():
    db = MagicMock()
    mock_device = MagicMock(id=1, code="device_key_101")
    db.query.return_value.filter.return_value.first.return_value = mock_device

    found_device = mdevice.Device.get_by_id(db, dev_id=1)
    assert found_device.id == 1
    assert found_device.code == "device_key_101"


def test_get_by_code_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as excinfo:
        mdevice.Device.get_by_code(db, dev_code="InvalidCode")
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Device with code: InvalidCode doesn't exist"


def test_get_by_code_found():
    db = MagicMock()
    mock_device = MagicMock(code="device_key_101")
    db.query.return_value.filter.return_value.first.return_value = mock_device

    found_device = mdevice.Device.get_by_code(db, dev_code="device_key_101")
    assert found_device.code == "device_key_101"


def test_create_session_success():
    db = MagicMock()
    session = moperation.UserSession.create_session(
        db, user_id=1, concierge_id=2, commit=False)

    assert session.user_id == 1
    assert session.concierge_id == 2
    assert session.status == "w trakcie"
    assert isinstance(session.start_time, datetime.datetime)


def test_end_session_success():
    db = MagicMock()
    mock_session = MagicMock(id=1, status="w trakcie", end_time=None)
    db.query.return_value.filter_by.return_value.first.return_value = mock_session

    ended_session = moperation.UserSession.end_session(db, session_id=1)
    assert ended_session.status == "potwierdzona"
    assert isinstance(ended_session.end_time, datetime.datetime)


def test_get_all_users_no_users():
    db = MagicMock()
    db.query.return_value.all.return_value = []

    with pytest.raises(HTTPException) as excinfo:
        User.get_all_users(db)
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "There is no user in the database"


def test_get_user_id_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as excinfo:
        User.get_user_id(db, user_id=-1)
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "User with id: -1 doesn't exist"


def test_create_or_get_unauthorized_user_existing():
    db = MagicMock()
    mock_user = UnauthorizedUser(
        name="John", surname="Doe", email="john@example.com")
    db.query.return_value.filter_by.return_value.first.return_value = mock_user

    user, created = UnauthorizedUser.create_or_get_unauthorized_user(
        db, name="John", surname="Doe", email="john@example.com"
    )
    assert user == mock_user
    assert not created


def test_create_or_get_unauthorized_user_new():
    db = MagicMock()
    db.query.return_value.filter_by.return_value.first.return_value = None

    new_user, created = UnauthorizedUser.create_or_get_unauthorized_user(
        db, name="Jane", surname="Joe", email="jane.joe@edu.pl"
    )
    assert created
    db.add.assert_called_once_with(new_user)
    db.commit.assert_called_once()


def test_create_or_get_unauthorized_user_conflict():
    db = MagicMock()
    existing_user = UnauthorizedUser(
        name="John", surname="Doe", email="john@example.com")
    db.query.return_value.filter_by.return_value.first.return_value = existing_user

    with pytest.raises(HTTPException) as excinfo:
        UnauthorizedUser.create_or_get_unauthorized_user(
            db, name="Jane", surname="Doe", email="john@example.com"
        )
    assert excinfo.value.status_code == 409
    detail: dict[str, Any] = excinfo.value.detail
    assert isinstance(detail, dict)
    assert detail['message'] == "User with this email already exists but with a different name or surname."

def test_get_user_notes_filter_no_notes():
    db = MagicMock()
    db.query.return_value.filter.return_value.all.return_value = []

    with pytest.raises(HTTPException) as excinfo:
        UserNote.get_user_notes_filter(db, user_id=1)
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "No user notes found."


def test_create_user_note_success():
    db = MagicMock()
    note_data = schemas.UserNoteCreate(user_id=1, note="This is a test note")

    note = UserNote.create_user_note(
        db, note_data=note_data
    )
    assert note.note == "This is a test note"
    assert isinstance(note.timestamp, datetime.datetime)
    db.add.assert_called_once_with(note)
    db.commit.assert_called_once()


def test_create_user_note_empty_note():
    db = MagicMock()
    note_data = schemas.UserNoteCreate(user_id=1, note="")
    with pytest.raises(ValueError):
        UserNote.create_user_note(db, note_data=note_data)


def test_update_user_note_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as excinfo:
        UserNote.update_user_note(
            db, note_id=1, note_data=schemas.NoteUpdate(note="Updated note"))
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Note with id 1 not found"


def test_delete_user_note_success():
    db = MagicMock()
    mock_note = UserNote(id=1, note="To be deleted")
    db.query.return_value.filter.return_value.first.return_value = mock_note

    UserNote.delete_user_note(db, note_id=1)
    db.delete.assert_called_once_with(mock_note)
    db.commit.assert_called_once()


def test_permission_get_permissions_with_filters():
    db = MagicMock()
    mock_permission = Permission(
        id=1, user_id=1, room_id=101, date=datetime.date.today())

    query_mock = db.query.return_value
    query_mock.filter.return_value = query_mock
    query_mock.order_by.return_value = query_mock
    query_mock.all.return_value = [mock_permission]

    permissions = Permission.get_permissions(
        db, user_id=1, room_id=101, date=datetime.date.today())
    assert len(permissions) == 1
    assert permissions[0].user_id == 1
    assert permissions[0].room_id == 101


def test_permission_get_permissions_no_permissions():
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

    with pytest.raises(HTTPException) as excinfo:
        Permission.get_permissions(db)
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "No reservations found"


def test_hash_password():
    password_service = PasswordService()
    password = "supersecret"
    hashed_password = password_service.hash_password(password)
    assert hashed_password != password
    assert password_service.verify_hashed(password, hashed_password)


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


@patch("jose.jwt.decode")
def test_verify_concierge_token_valid(mock_jwt_decode: Any):
    mock_jwt_decode.return_value = {"user_id": 1, "user_role": "concierge"}
    db = MagicMock()
    token_service = TokenService(db)
    token = "sometoken"
    token_data = token_service.verify_concierge_token(token)
    assert token_data.id == 1
    assert token_data.role == "concierge"


@patch("jose.jwt.decode", side_effect=JWTError)
def test_verify_concierge_token_invalid(mock_jwt_decode: Any):
    db = MagicMock()
    token_service = TokenService(db)
    token = "invalidtoken"

    with pytest.raises(HTTPException) as excinfo:
        token_service.verify_concierge_token(token)
    assert excinfo.value.status_code == 401
    assert excinfo.value.detail == "Invalid token"


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


def test_add_token_to_blacklist():
    db = MagicMock()
    db.query.return_value.filter_by.return_value.first.return_value = None
    token_service = TokenService(db)
    token_service.add_token_to_blacklist("blacklisted_token")
    db.add.assert_called_once()
    db.commit.assert_called_once()


def test_entitled_or_error_user_has_role():
    db = MagicMock()
    auth_service = AuthorizationService(db)
    user = User(role=UserRole.concierge)
    auth_service.entitled_or_error("concierge", user)


def test_entitled_or_error_user_no_role():
    db = MagicMock()
    auth_service = AuthorizationService(db)
    user = User(role=UserRole.employee)

    with pytest.raises(HTTPException) as excinfo:
        auth_service.entitled_or_error("admin", user)
    assert excinfo.value.status_code == 403
    assert excinfo.value.detail == "You cannot perform this operation without the admin role"


@patch.object(TokenService, "is_token_blacklisted", return_value=True)
def test_get_current_concierge_blacklisted_token(mock_is_blacklisted: Any):
    db = MagicMock()
    auth_service = AuthorizationService(db)
    token = "blacklisted_token"

    with pytest.raises(HTTPException) as excinfo:
        auth_service.get_current_concierge(token)
    assert excinfo.value.status_code == 403
    assert excinfo.value.detail == "You are logged out"


@patch.object(TokenService, "is_token_blacklisted", return_value=False)
@patch.object(TokenService, "verify_concierge_token")
def test_get_current_concierge_user_not_found(mock_verify_token: Any, mock_is_token_blacklisted: Any):
    mock_verify_token.return_value = schemas.TokenData(id=1, role="concierge")
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    auth_service = AuthorizationService(db)
    token = "valid_token"

    with pytest.raises(HTTPException) as excinfo:
        auth_service.get_current_concierge(token)
    assert excinfo.value.status_code == 401
    assert excinfo.value.detail == "Could not validate credentials"


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
