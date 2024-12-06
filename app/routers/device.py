from fastapi import status, Depends, APIRouter
from typing import Optional, Sequence, List, Literal
from app import database, oauth2, schemas
import app.models.device as mdevice
from app.services import securityService
from sqlalchemy.orm import Session
from app.models.user import User
from app.config import logger
import app.models.user as muser
from fastapi import Response

router = APIRouter(
    prefix="/devices",
    tags=['Devices']
)


@router.get("/", response_model=List[schemas.DeviceOutWithNote], responses={
    404: {
        "description": "If no devices match the specified criteria.",
        "content": {
            "application/json": {
                "example": {
                    "detail": "No devices found matching criteria"
                }
            }
        }
    },
})
def get_devices_filtered(response: Response,
                         current_concierge: User = Depends(oauth2.get_current_concierge),
                         dev_type: Optional[Literal["klucz",
                                                    "mikrofon", "pilot"]] = None,
                         dev_version: Optional[Literal["podstawowa",
                                                       "zapasowa"]] = None,
                         room_number: Optional[str] = None,
                         db: Session = Depends(database.get_db)) -> List[schemas.DeviceOutWithNote]:
    """
    Retrieves detailed information for devices, including related data such as room number, ownership status, and notes.
    Filters can be applied based on device type, version, and room number. 
    """
    logger.info(
        f"GET request to retrieve devices by type {dev_type}, version {dev_version} and room number {room_number}.")

    devices = mdevice.Device.get_dev_with_details(
        db, dev_type, dev_version, room_number)
    oauth2.set_access_token_cookie(response, current_concierge.id, current_concierge.role.value, db)
    return [schemas.DeviceOutWithNote.model_validate(device) for device in devices]


@router.get("/code/{dev_code}", response_model=schemas.DeviceOut, responses={
    404: {
        "description": "If no device with the given code exists",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Device not found"
                }
            }
        }
    },
})
def get_dev_code(response: Response,
                 dev_code: str,
                 current_concierge: User = Depends(
                     oauth2.get_current_concierge),
                 db: Session = Depends(database.get_db)) -> schemas.DeviceOut:
    """
    Retrieve a device by its unique device code.
    """
    logger.info(f"GET request to retrieve device by code {dev_code}.")
    oauth2.set_access_token_cookie(response, current_concierge.id, current_concierge.role.value, db)
    return mdevice.Device.get_dev_by_code(db, dev_code)


@router.get("/{dev_id}", response_model=schemas.DeviceOut, responses={
    404: {
        "description": "If no device with the given ID exists",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Device not found"
                }
            }
        }
    },
})
def get_dev_id(response: Response,
               dev_id: int,
               current_concierge: User = Depends(
                   oauth2.get_current_concierge),
               db: Session = Depends(database.get_db)) -> schemas.DeviceOut:
    """
    Retrieve a device by its unique device code.

    This endpoint retrieves a device from the database using the device's unique code.
    """
    logger.info(f"GET request to retrieve device with Id {dev_id}.")
    oauth2.set_access_token_cookie(response, current_concierge.id, current_concierge.role.value, db)
    return mdevice.Device.get_dev_by_id(db, dev_id)


@router.post("/", response_model=schemas.DeviceOut, status_code=status.HTTP_201_CREATED, responses={
    500: {
        "description": "If an error occurs during the commit",
        "content": {
            "application/json": {
                "example": {
                    "detail": "An internal error occurred while creating device"
                }
            }
        }
    },
    403: {
        "description": "If the user does not have the required role or higher",
        "content": {
            "application/json": {
                "example": {
                    "detail": "You cannot perform this operation without the appropriate role"
                }
            }
        }
    },
})
def create_device(response: Response,
                  device: schemas.DeviceCreate,
                  db: Session = Depends(database.get_db),
                  current_concierge: User = Depends(oauth2.get_current_concierge)) -> schemas.DeviceOut:
    """
    Create a new device in the database.

    This endpoint allows to create a new device by providing the necessary
    data. Only users with the 'admin' role are permitted to create devices.
    """
    logger.info(f"POST request to create device")

    auth_service = securityService.AuthorizationService(db)
    auth_service.entitled_or_error(muser.UserRole.admin, current_concierge)
    oauth2.set_access_token_cookie(response, current_concierge.id, current_concierge.role.value, db)
    return mdevice.Device.create_dev(db, device)


@router.put("/{device_id}", response_model=schemas.DeviceOut, responses={
    500: {
        "description": "If an error occurs during the commit",
        "content": {
            "application/json": {
                "example": {
                    "detail": "An internal error occurred while updating device"
                }
            }
        }
    },
    403: {
        "description": "If the user does not have the required role or higher",
        "content": {
            "application/json": {
                "example": {
                    "detail": "You cannot perform this operation without the appropriate role"
                }
            }
        }
    },
})
def update_device(
    response: Response,
    device_id: int,
    device_data: schemas.DeviceCreate,
    current_concierge: User = Depends(
        oauth2.get_current_concierge),
    db: Session = Depends(database.get_db)
) -> Sequence[schemas.DeviceOut]:
    """
    Updates an existing device in the database.

    This endpoint allows to update device by providing new
    data. Only users with the 'admin' role are permitted to update devices.
    """
    logger.info(f"PUT request to update device")
    auth_service = securityService.AuthorizationService(db)
    auth_service.entitled_or_error(muser.UserRole.admin, current_concierge)
    oauth2.set_access_token_cookie(response, current_concierge.id, current_concierge.role.value, db)
    return mdevice.Device.update_dev(db, device_id, device_data)


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT, responses={
    500: {
        "description": "If an error occurs during the commit",
        "content": {
            "application/json": {
                "example": {
                    "detail": "An internal error occurred while deleting device"
                }
            }
        }
    },
    403: {
        "description": "If the user does not have the required role or higher",
        "content": {
            "application/json": {
                "example": {
                    "detail": "You cannot perform this operation without the appropriate role"
                }
            }
        }
    },
})
def delete_device(
    response: Response,
    device_id: int,
    current_concierge: User = Depends(
        oauth2.get_current_concierge),
    db: Session = Depends(database.get_db)
):
    """
    Deletes a device by its unique ID from the database.

    This endpoint allows to delete device from database. 
    Only users with the 'admin' role are permitted to delete devices.
    """
    logger.info(f"DELETE request to delete device with ID {device_id}")
    auth_service = securityService.AuthorizationService(db)
    auth_service.entitled_or_error(muser.UserRole.admin, current_concierge)
    oauth2.set_access_token_cookie(response, current_concierge.id, current_concierge.role.value, db)
    return mdevice.Device.delete_dev(db, device_id)
