import sys
import os
import pytest
import datetime
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Any, Generator
from app import database, schemas
import app.models.user as muser
import app.models.device as mdevice
import app.models.permission as mpermission
import app.models.operation as moperation
from app.services import securityService
from app.models.base import Base

sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', '..')))


@pytest.fixture(scope="module")
def db() -> Generator[Session, None, None]:
    session = database.SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="module")
def test_concierge(db: Session) -> muser.User:
    user_data = schemas.UserCreate(
        email="testconcierge@example.com",
        password="password123",
        card_code="123456",
        role="administrator",
        name="Test",
        surname="Concierge",
        faculty="Geodezji i Kartografii"
    )
    password_service = securityService.PasswordService()
    user_data.password = password_service.hash_password(user_data.password)
    user_data.card_code = password_service.hash_password(user_data.card_code)

    user = muser.User(**user_data.model_dump())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="module")
def test_user(db: Session) -> muser.User:
    user_data = schemas.UserCreate(
        email="testuser@example.com",
        password="password456",
        card_code="7890",
        role="pracownik",
        name="Test",
        surname="User",
        faculty="Geodezji i Kartografii"
    )
    password_service = securityService.PasswordService()
    user_data.password = password_service.hash_password(user_data.password)
    user_data.card_code = password_service.hash_password(user_data.card_code)

    user = muser.User(**user_data.model_dump())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture(scope="module")
def test_unauthorized_user(db: Session) -> muser.UnauthorizedUser:
    unauthorized_user = muser.UnauthorizedUser(
        id=1,
        name="John",
        surname="Doe",
        email="john.doe@example.com",
        added_at=datetime.datetime.now()
    )
    db.add(unauthorized_user)
    db.commit()
    return unauthorized_user


@pytest.fixture(scope="module")
def test_room(db: Session) -> mdevice.Room:
    room = mdevice.Room(number="101")
    db.add(room)
    db.commit()
    db.refresh(room)
    return room


@pytest.fixture(scope="module")
def test_room_2(db: Session) -> mdevice.Room:
    room = mdevice.Room(number="102")
    db.add(room)
    db.commit()
    db.refresh(room)
    return room


@pytest.fixture(scope="module")
def test_permission(db: Session, test_user: muser.User, test_room: mdevice.Room) -> mpermission.Permission:
    now = datetime.datetime.now()
    start_time = (now - datetime.timedelta(hours=1))
    end_time = (now + datetime.timedelta(hours=1))
    if start_time.date() < now.date():
        start_time = datetime.datetime.combine(
            now.date(), datetime.time(0, 0))

    if end_time.date() > now.date():
        end_time = datetime.datetime.combine(
            now.date(), datetime.time(23, 59))

    assert start_time.date() == now.date()
    assert end_time.date() == now.date()
    assert end_time > start_time

    permission = mpermission.Permission(
        user_id=test_user.id,
        room_id=test_room.id,
        date=datetime.date.today(),
        start_time=start_time.time(),
        end_time=end_time.time()
    )
    db.add(permission)
    db.commit()
    db.refresh(permission)
    return permission

@pytest.fixture(scope="module")
def test_permission_2(db: Session, 
                      test_user: muser.User, 
                      test_room_2: mdevice.Room) -> mpermission.Permission:
    now = datetime.datetime.now()
    start_time = (now - datetime.timedelta(hours=1))
    end_time = (now + datetime.timedelta(hours=1))
    if start_time.date() < now.date():
        start_time = datetime.datetime.combine(
            now.date(), datetime.time(0, 0))

    if end_time.date() > now.date():
        end_time = datetime.datetime.combine(
            now.date(), datetime.time(23, 59))

    assert start_time.date() == now.date()
    assert end_time.date() == now.date()
    assert end_time > start_time

    permission = mpermission.Permission(
        user_id=test_user.id,
        room_id=test_room_2.id,
        date=datetime.date.today(),
        start_time=start_time.time(),
        end_time=end_time.time()
    )
    db.add(permission)
    db.commit()
    db.refresh(permission)
    return permission

@pytest.fixture(scope="module")
def test_session(db: Session, test_user: muser.User, test_concierge: muser.User) -> moperation.UserSession:
    session = moperation.UserSession(
        user_id=test_user.id,
        concierge_id=test_concierge.id,
        start_time=datetime.datetime(
            2024, 12, 6, 12, 45, tzinfo=ZoneInfo("Europe/Warsaw")).isoformat(),
        status="w trakcie"
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@pytest.fixture(scope="module")
def test_device(db: Session, test_room: mdevice.Room) -> mdevice.Device:
    device = mdevice.Device(
        dev_type="klucz",
        room_id=test_room.id,
        dev_version="podstawowa",
        code="device_key_101"
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


@pytest.fixture(scope="module")
def test_device_microphone(db: Session, test_room_2: mdevice.Room) -> mdevice.Device:
    device = mdevice.Device(
        dev_type="mikrofon",
        room_id=test_room_2.id,
        dev_version="zapasowa",
        code="device_mic_101"
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


@pytest.fixture
def test_user_note(db: Session, test_user: muser.User) -> muser.UserNote:
    note = muser.UserNote(user_id=test_user.id,
                          note="Test Note", timestamp=datetime.datetime.now())
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@pytest.fixture
def test_specific_user_note(db: Session, test_user: muser.User) -> muser.UserNote:
    note = muser.UserNote(
        user_id=test_user.id, note="Test Specific Note", timestamp=datetime.datetime.now())
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@pytest.fixture
def test_device_note(db: Session, test_device: mdevice.Device, test_session: moperation.UserSession) -> mdevice.DeviceNote:
    note = mdevice.DeviceNote(
        device_id=test_device.id, note="Device note content", timestamp=datetime.datetime.now())
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@pytest.fixture
def test_operation(db: Session, test_device: mdevice.Device, test_session: moperation.UserSession) -> mdevice.DeviceNote:
    note = moperation.DeviceOperation(
        device_id=test_device.id, session_id=test_session.id, operation_type="pobranie", entitled=True, timestamp=datetime.datetime.now())
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@pytest.fixture(scope="module", autouse=True)
def cleanup_db_after_tests(db: Session) -> Generator[None, None, None]:
    yield
    db.execute(text("SET session_replication_role = 'replica';"))

    for table in reversed(Base.metadata.sorted_tables):
        db.execute(table.delete())

    db.commit()
    db.execute(text("SET session_replication_role = 'origin';"))


@pytest.fixture(scope="module")
def concierge_token(db: Session, test_concierge: muser.User) -> str:
    token_service = securityService.TokenService(db)
    token_data: dict[str, Any] = {
        'user_id': test_concierge.id, 'user_role': test_concierge.role.value}
    token = token_service.create_token(token_data, token_type="access")
    return token


@pytest.fixture(scope="module")
def concierge_refresh_token(db: Session, test_concierge: muser.User) -> str:
    token_service = securityService.TokenService(db)
    token_data: dict[str, Any] = {
        'user_id': test_concierge.id, 'user_role': test_concierge.role.value}
    token = token_service.create_token(token_data, token_type="refresh")
    return token
