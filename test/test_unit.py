import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException
import app.models.device as mdevice
import datetime
import app.models.operation as moperation

# Testy dla metody get_rooms
def test_get_rooms_no_rooms():
    # Tworzymy mock bazy danych
    db = MagicMock()
    db.query.return_value.all.return_value = []

    with pytest.raises(HTTPException) as excinfo:
        mdevice.Room.get_rooms(db)
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "There is no room in database"

def test_get_rooms_with_rooms():
    # Tworzymy mock bazy danych i przykład pokoju
    db = MagicMock()
    mock_room = mdevice.Room(id=1, number="101")
    db.query.return_value.all.return_value = [mock_room]

    rooms = mdevice.Room.get_rooms(db)
    assert len(rooms) == 1
    assert rooms[0].number == "101"

def test_get_rooms_with_specific_number():
    # Tworzymy mock bazy danych i przykład pokoju
    db = MagicMock()
    mock_room = mdevice.Room(id=1, number="101")
    db.query.return_value.filter.return_value.all.return_value = [mock_room]

    rooms = mdevice.Room.get_rooms(db, room_number="101")
    assert len(rooms) == 1
    assert rooms[0].number == "101"

def test_get_room_id_not_found():
    # Tworzymy mock bazy danych
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as excinfo:
        mdevice.Room.get_room_id(db, room_id=-1)
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Room with id: -1 doesn't exist"

def test_get_room_id_found():
    # Tworzymy mock bazy danych i przykład pokoju
    db = MagicMock()
    mock_room = mdevice.Room(id=1, number="101")
    db.query.return_value.filter.return_value.first.return_value = mock_room

    room = mdevice.Room.get_room_id(db, room_id=1)
    assert room.id == 1
    assert room.number == "101"

def test_get_room_number_not_found():
    # Tworzymy mock bazy danych
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as excinfo:
        mdevice.Room.get_room_number(db, room_number="InvalidNumber")
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Room number: InvalidNumber doesn't exist"

def test_get_room_number_found():
    # Tworzymy mock bazy danych i przykład pokoju
    db = MagicMock()
    mock_room = mdevice.Room(id=2, number="102")
    db.query.return_value.filter.return_value.first.return_value = mock_room

    room = mdevice.Room.get_room_number(db, room_number="102")
    assert room.number == "102"

def test_get_device_with_details_no_devices():
    # Tworzymy mock bazy danych
    db = MagicMock()
    
    # Konfigurujemy, aby `all()` zwracało pustą listę, co powinno spowodować podniesienie wyjątku
    db.query.return_value.all.return_value = []

    # Wywołujemy metodę i sprawdzamy, czy podnosi wyjątek HTTPException
    with pytest.raises(HTTPException) as excinfo:
        mdevice.Device.get_device_with_details(db)
    
    # Sprawdzamy, czy wyjątek ma odpowiedni kod statusu i szczegóły
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "There are no devices that match the given criteria in the database"

def test_get_device_with_details_with_criteria():
    db = MagicMock()

    mock_device = MagicMock(code="device_key_101", dev_type="key", dev_version="primary")

    query_mock = db.query.return_value
    query_mock.join.return_value = query_mock
    query_mock.outerjoin.return_value = query_mock
    query_mock.filter.return_value = query_mock
    query_mock.group_by.return_value = query_mock
    query_mock.order_by.return_value = query_mock
    query_mock.all.return_value = [mock_device]

    devices = mdevice.Device.get_device_with_details(db, dev_type="key")

    assert len(devices) > 0
    assert "device_key_101" in [d.code for d in devices]

# Test dla niepoprawnego typu urządzenia
def test_get_device_with_invalid_type():
    db = MagicMock()

    with pytest.raises(HTTPException) as excinfo:
        mdevice.Device.get_device_with_details(db, dev_type="InvalidType")
    assert excinfo.value.status_code == 400
    assert excinfo.value.detail == "Invalid device type: InvalidType"

# Test dla niepoprawnej wersji urządzenia
def test_get_device_with_invalid_version():
    db = MagicMock()

    with pytest.raises(HTTPException) as excinfo:
        mdevice.Device.get_device_with_details(db, dev_version="InvalidVersion")
    assert excinfo.value.status_code == 400
    assert excinfo.value.detail == "Invalid device version: InvalidVersion"

# Test dla nieistniejącego ID urządzenia
def test_get_by_id_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as excinfo:
        mdevice.Device.get_by_id(db, dev_id=-1)
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Device with id: -1 doesn't exist"

# Test dla istniejącego ID urządzenia
def test_get_by_id_found():
    db = MagicMock()
    mock_device = MagicMock(id=1, code="device_key_101")
    db.query.return_value.filter.return_value.first.return_value = mock_device

    found_device = mdevice.Device.get_by_id(db, dev_id=1)
    assert found_device.id == 1
    assert found_device.code == "device_key_101"

# Test dla nieistniejącego kodu urządzenia
def test_get_by_code_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as excinfo:
        mdevice.Device.get_by_code(db, dev_code="InvalidCode")
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Device with code: InvalidCode doesn't exist"

# Test dla istniejącego kodu urządzenia
def test_get_by_code_found():
    db = MagicMock()
    mock_device = MagicMock(code="device_key_101")
    db.query.return_value.filter.return_value.first.return_value = mock_device

    found_device = mdevice.Device.get_by_code(db, dev_code="device_key_101")
    assert found_device.code == "device_key_101"

# Test udanego utworzenia sesji
def test_create_session_success():
    db = MagicMock()
    session = moperation.UserSession.create_session(db, user_id=1, concierge_id=2, commit=False)

    assert session.user_id == 1
    assert session.concierge_id == 2
    assert session.status == "w trakcie"
    assert isinstance(session.start_time, datetime.datetime)

# Test zakończenia sesji
def test_end_session_success():
    db = MagicMock()
    mock_session = MagicMock(id=1, status="w trakcie", end_time=None)
    db.query.return_value.filter_by.return_value.first.return_value = mock_session

    ended_session = moperation.UserSession.end_session(db, session_id=1)
    assert ended_session.status == "potwierdzona"
    assert isinstance(ended_session.end_time, datetime.datetime)
