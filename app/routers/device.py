from fastapi import status, Depends, APIRouter
from typing import Optional, Sequence, List, Literal
from app import database, oauth2, schemas
import app.models.device as mdevice
from app.services import securityService
from sqlalchemy.orm import Session
from app.models.user import User
from app.config import logger

router = APIRouter(
    prefix="/devices",
    tags=['Devices']
)


@router.get("/", response_model=List[schemas.DeviceOutWithNote])
def get_devices_filtered(current_concierge: User = Depends(oauth2.get_current_concierge),
                         dev_type: Optional[Literal["klucz",
                                                    "mikrofon", "pilot"]] = None,
                         dev_version: Optional[Literal["podstawowa",
                                                       "zapasowa"]] = None,
                         room_number: Optional[str] = None,
                         db: Session = Depends(database.get_db)) -> List[schemas.DeviceOutWithNote]:
    """
    Retrieve all devices from the database, optionally filtered by type or dev_version.

    This endpoint retrieves a list of devices from the database. Optionally,
    the list can be filtered by device type and dev_version if these parameters are provided.
    """
    logger.info(
        f"GET request to retrieve devices by type {dev_type}, version {dev_version} and room number {room_number}.")

    devices = mdevice.Device.get_dev_with_details(
        db, dev_type, dev_version, room_number)
    return [schemas.DeviceOutWithNote.model_validate(device) for device in devices]


@router.get("/code/{dev_code}", response_model=schemas.DeviceOut)
def get_dev_code(dev_code: str,
                 current_concierge: User = Depends(
                     oauth2.get_current_concierge),
                 db: Session = Depends(database.get_db)) -> schemas.DeviceOut:
    """
    Retrieve a device by its unique device code.

    This endpoint retrieves a device from the database using the device's unique code.
    """
    logger.info(f"GET request to retrieve device by code {dev_code}.")

    return mdevice.Device.get_dev_by_code(db, dev_code)


@router.get("/{dev_id}", response_model=schemas.DeviceOut)
def get_dev_id(dev_id: int,
               current_concierge: User = Depends(
                   oauth2.get_current_concierge),
               db: Session = Depends(database.get_db)) -> schemas.DeviceOut:
    """
    Retrieve a device by its unique device code.

    This endpoint retrieves a device from the database using the device's unique code.
    """
    logger.info(f"GET request to retrieve device by Id {dev_id}.")

    return mdevice.Device.get_dev_by_id(db, dev_id)


@router.post("/", response_model=schemas.DeviceOut, status_code=status.HTTP_201_CREATED)
def create_device(device: schemas.DeviceCreate,
                  db: Session = Depends(database.get_db),
                  current_concierge: User = Depends(oauth2.get_current_concierge)) -> schemas.DeviceOut:
    """
    Create a new device in the database.

    This endpoint allows concierge to create a new device by providing the necessary
    data. Only users with the 'admin' role are permitted to create devices.
    """
    logger.info(f"POST request to create device with data {device}")

    auth_service = securityService.AuthorizationService(db)
    auth_service.entitled_or_error("admin", current_concierge)
    return mdevice.Device.create_dev(db, device)

@router.put("/{device_id}", response_model=schemas.DeviceOut)
def update_device(
    device_id: int,
    device_data: schemas.DeviceCreate,
    current_concierge: User = Depends(
        oauth2.get_current_concierge),
    db: Session = Depends(database.get_db)
) -> Sequence[schemas.DeviceOut]:
    """
    Aktualizuje dane urządzenia o podanym `device_id`.

    Args:
        device_id (int): ID urządzenia do zaktualizowania.
        device_data (DeviceUpdate): Dane do zaktualizowania.
        db (Session): Sesja bazy danych.

    Returns:
        DeviceResponse: Zaktualizowany obiekt urządzenia.
    """
    return mdevice.Device.update_dev(db, device_id, device_data)


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device(
    device_id: int,
    current_concierge: User = Depends(
        oauth2.get_current_concierge),
    db: Session = Depends(database.get_db)
):
    """
    Usuwa urządzenie o podanym `device_id`.

    Args:
        device_id (int): ID urządzenia do usunięcia.
        db (Session): Sesja bazy danych.
    """
    auth_service = securityService.AuthorizationService(db)
    auth_service.entitled_or_error("admin", current_concierge)
    return mdevice.Device.delete_dev(db, device_id)
