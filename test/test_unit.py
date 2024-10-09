import pytest
from unittest.mock import MagicMock
from app.services import deviceService
from app.schemas import DeviceCreate
from app import models
from fastapi import HTTPException


@pytest.fixture
def mock_db():
    mock_session = MagicMock()
    return mock_session


def test_create_device(mock_db):
    device_data = DeviceCreate(
        version="primary", is_taken=False, dev_type="key", code="A123", room_id=1)
    device_service = deviceService.DeviceService(mock_db)

    created_device = device_service.create_dev(device_data)

    mock_db.add.assert_called_once()
    assert created_device.version == "primary"
    assert created_device.is_taken is False
    assert created_device.dev_type == "key"
    assert created_device.code == "A123"


def test_get_dev_code(mock_db):
    device_service = deviceService.DeviceService(mock_db)
    mock_device = models.Device(
        code="A123", dev_type="key", version="primary", room_id=1)
    mock_db.query().filter().first.return_value = mock_device

    device = device_service.get_dev_code("A123")

    assert device.code == "A123"
    mock_db.query().filter().first.assert_called_once()


def test_get_dev_code_not_found(mock_db):
    device_service = deviceService.DeviceService(mock_db)
    mock_db.query().filter().first.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        device_service.get_dev_code("XYZ")
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Device with code: XYZ doesn't exist"


def test_get_all_devs(mock_db):
    device_service = deviceService.DeviceService(mock_db)
    mock_device = models.Device(
        code="A123", dev_type="key", version="primary", room_id=1)
    mock_db.query().filter().filter().all.return_value = [mock_device]
    devices = device_service.get_all_devs(
        dev_type="key", dev_version="primary")
    assert len(devices) == 1
    assert devices[0].code == "A123"
    mock_db.query().filter().filter().all.assert_called_once()


def test_get_all_devs_not_found(mock_db):
    device_service = deviceService.DeviceService(mock_db)
    mock_db.query().filter().filter().all.return_value = []
    with pytest.raises(HTTPException) as exc_info:
        device_service.get_all_devs(dev_type="key", dev_version="primary")
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "There are no devices that match the given criteria in the database"
    mock_db.query().filter().filter().all.assert_called_once()


def test_get_unapproved_device_by_code(mock_db):
    unapproved_service = deviceService.UnapprovedDeviceService(mock_db)
    mock_device = models.DeviceUnapproved(device_id=1)
    mock_db.query().filter().first.return_value = mock_device

    device = unapproved_service.get_dev_id(1)

    assert device.device_id == 1
    mock_db.query().filter().first.assert_called_once()


def test_get_unapproved_device_by_code_not_found(mock_db):
    unapproved_service = deviceService.UnapprovedDeviceService(mock_db)
    mock_db.query().filter().first.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        unapproved_service.get_dev_id(4)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Device with id: 4 doesn't exist"


def test_create_unapproved_device(mock_db):
    unapproved_service = deviceService.UnapprovedDeviceService(mock_db)
    unapproved_data = {"device_id": 2,
                       "is_taken": False, "issue_return_session_id": 1}

    new_device = unapproved_service.create_unapproved(unapproved_data)

    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    assert new_device.device_id == 2
    assert new_device.is_taken is False
