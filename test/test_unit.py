import pytest
from unittest.mock import MagicMock
from app.services.deviceService import DeviceService
from app.schemas import DeviceCreate


@pytest.fixture
def mock_db():
    mock_session = MagicMock()
    return mock_session


def test_create_device(mock_db):
    device_data = DeviceCreate(version="primary", is_taken=False, type="key", code="A123", room_id=1)

    device_service = DeviceService(mock_db)

    created_device = device_service.create_dev(device_data)

    mock_db.add.assert_called_once()

    assert created_device.version == "primary"
    assert created_device.is_taken is False
    assert created_device.type == "key"
    assert created_device.code == "A123"
    assert created_device.room_id == 1
