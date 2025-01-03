from fastapi import status, Depends, APIRouter, Query
from typing import Optional, Sequence, List, Literal
from app import database, oauth2, schemas
import app.models.device as mdevice
from app.services import securityService
from sqlalchemy.orm import Session
from app.models.user import User
from app.config import logger
import app.models.user as muser
from fastapi import HTTPException

router = APIRouter(
    prefix="/devices",
    tags=['Devices']
)


@router.get("/", response_model=List[schemas.DeviceOutWithNote], responses={
    204: {
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
def get_devices_filtered(current_concierge: User = Depends(oauth2.get_current_concierge),
                         dev_type: Optional[Literal["klucz",
                                                    "mikrofon", "pilot"]] = Query(
        None, description="Filter devices by type. Possible values: 'klucz', 'mikrofon', 'pilot'."
    ),
                         dev_version: Optional[Literal["podstawowa",
                                                       "zapasowa"]] = Query(
        None, description="Filter devices by version. Possible values: 'podstawowa', 'zapasowa'."
    ),
                         room_number: Optional[str] = Query(
        None, description="Filter devices by room number."
    ),
                         db: Session = Depends(database.get_db)) -> List[schemas.DeviceOutWithNote]:
    """
    Retrieve a list of devices with detailed information, including their type, version,
    associated notes and availability status .This endpoint allows filtering devices based on specific criteria, 
    such as type, version, or room number. If no devices match the criteria, 
    a 404 response is returned with a descriptive error message.

    """
    logger.info(
        f"GET request to retrieve devices by type {dev_type}, version {dev_version} and room number {room_number}.")
    
    devices = mdevice.Device.get_dev_with_details(
        db, dev_type, dev_version, room_number)
    return [schemas.DeviceOutWithNote.model_validate(device) for device in devices]


@router.get("/code/{dev_code}", response_model=schemas.DeviceOut, responses={
    204: {
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
def get_dev_code(dev_code: str,
                 current_concierge: User = Depends(
                     oauth2.get_current_concierge),
                 db: Session = Depends(database.get_db)) -> schemas.DeviceOut:
    """
    Retrieve detailed information about a specific device based on its unique code. 
    This endpoint is useful for fetching precise device data, including its status. 
    If the device does not exist in the database, 
    a 404 response is returned with an appropriate error message.

    """
    logger.info(f"GET request to retrieve device by code {dev_code}.")

    device = mdevice.Device.get_dev_by_code(db, dev_code)
    
    if not device:
            logger.warning(f"Device with code {dev_code} not found.")
            raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)
    
    return device


@router.get("/{dev_id}", response_model=schemas.DeviceOut, responses={
    204: {
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
def get_dev_id(dev_id: int,
               current_concierge: User = Depends(
                   oauth2.get_current_concierge),
               db: Session = Depends(database.get_db)) -> schemas.DeviceOut:
    """
    Retrieve detailed information about a specific device based on its ID. 
    This endpoint is useful for fetching precise device data, including its status. 
    If the device does not exist in the database, 
    a 404 response is returned with an appropriate error message.

    """
    logger.info(f"GET request to retrieve device with Id {dev_id}.")
    device = mdevice.Device.get_dev_by_id(db, dev_id)
    if not device:
        logger.warning(f"Device with ID {dev_id} not found")
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)
    logger.debug(f"Device retrieved")

    return device


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
def create_device(device: schemas.DeviceCreate,
                  db: Session = Depends(database.get_db),
                  current_concierge: User = Depends(oauth2.get_current_concierge)) -> schemas.DeviceOut:
    """
    Create a new device in the system. This endpoint allows authorized users with the 
    'admin' role to add devices to the database by providing the necessary details, 
    such as type, version, and notes. 

    Upon successful creation, the endpoint returns the details of the created device. 
    If the user lacks the required role or if an error occurs during the database operation, 
    the appropriate error response is returned.

    """
    logger.info(f"POST request to create device")
    

    auth_service = securityService.AuthorizationService(db)
    auth_service.entitled_or_error(muser.UserRole.admin, current_concierge)
    return mdevice.Device.create_dev(db, device)


@router.post("/{device_id}", response_model=schemas.DeviceOut, responses={
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
def update_device(device_id: int,
                  device_data: schemas.DeviceCreate,
                  current_concierge: User = Depends(
                      oauth2.get_current_concierge),
                  db: Session = Depends(database.get_db)
) -> Sequence[schemas.DeviceOut]:
    """
    Update an existing device in the system.

    This endpoint allows authorized users with the 'admin' role to update the details 
    of an existing device identified by its unique ID. The new data for the device 
    is provided in the request body and includes details such as type, version, 
    and associated notes.

    Upon successful update, the endpoint returns the updated device's details. 
    If the user does not have the required role or if an error occurs during the 
    update operation, an appropriate error response is returned.

    """
    logger.info(f"POST request to update device")
    

    auth_service = securityService.AuthorizationService(db)
    auth_service.entitled_or_error(muser.UserRole.admin, current_concierge)
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
def delete_device(device_id: int,
                  current_concierge: User = Depends(oauth2.get_current_concierge),
                  db: Session = Depends(database.get_db)
):
    """
    Delete a device from the database using its unique ID. This endpoint ensures that 
    only users with the 'admin' role can perform deletion operations. 

    If the operation succeeds, a 204 No Content response is returned. If the user lacks 
    the required role or if an error occurs during the operation, an error response 
    is returned with the appropriate message.

    """
    logger.info(f"DELETE request to delete device with ID {device_id}")
    

    auth_service = securityService.AuthorizationService(db)
    auth_service.entitled_or_error(muser.UserRole.admin, current_concierge)
    
    return mdevice.Device.delete_dev(db, device_id)
