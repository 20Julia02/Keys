import datetime
from fastapi import status, Depends, APIRouter
from typing import List
from app.schemas import Token, DeviceCreate, DeviceOut, DetailMessage, DeviceOrDetailResponse
from app import database, oauth2
from app.services import deviceService, securityService, activityService
from sqlalchemy.orm import Session


router = APIRouter(
    prefix="/devices",
    tags=['Devices']
)


@router.get("/", response_model=List[DeviceOut])
def get_all_devices(current_concierge=Depends(oauth2.get_current_concierge),
                    dev_type: str = "",
                    db: Session = Depends(database.get_db)) -> List[DeviceOut]:
    """
    Retrieves all devices from the database that match the specified type.

    Args:
        current_concierge: The current user object (used for authorization).
        type (str): The type of device to filter by.
        db (Session): The database session.

    Returns:
        List[DeviceOut]: A list of devices that match the specified type.

    Raises:
        HTTPException: If no devices are found in the database.
    """
    dev_service = deviceService.DeviceService(db)
    return dev_service.get_all_devs(dev_type)


@router.get("/{id}", response_model=DeviceOut)
def get_dev_id(id: int,
               current_concierge=Depends(oauth2.get_current_concierge),
               db: Session = Depends(database.get_db)) -> DeviceOut:
    """
    Retrieves a device by its ID from the database.

    Args:
        id (int): The ID of the device.
        current_concierge: The current user object (used for authorization).
        db (Session): The database session.

    Returns:
        DeviceOut: The device with the specified ID.

    Raises:
        HTTPException: If the device with the specified ID doesn't exist.
    """
    dev_service = deviceService.DeviceService(db)
    return dev_service.get_dev_id(id)


@router.post("/", response_model=DeviceOut, status_code=status.HTTP_201_CREATED)
def create_device(device: DeviceCreate,
                  db: Session = Depends(database.get_db),
                  current_concierge=Depends(oauth2.get_current_concierge)) -> DeviceOut:
    """
    Creates a new device in the database.

    Args:
        device (DeviceCreate): The data required to create a new device.
        db (Session): The database session.
        current_concierge: The current user object (used for authorization).

    Returns:
        DeviceOut: The newly created device.

    Raises:
        HTTPException: If the user is not authorized to create a device.
    """
    auth_service = securityService.AuthorizationService(db)
    auth_service.check_if_entitled("admin", current_concierge)
    dev_service = deviceService.DeviceService(db)
    return dev_service.create_dev(device)


@router.post("/change-status/{id}", response_model=DeviceOrDetailResponse)
def change_status(
    token: Token,
    id: int,
    db: Session = Depends(database.get_db),
    current_concierge: int = Depends(oauth2.get_current_concierge),
) -> DeviceOrDetailResponse:
    """
    Changes the status of a device based on the provided token (with activity ID and user ID).
    It checks if the device has already been scanned for approval.
    If so, it removes the device from the unapproved data.
    Otherwise, it updates the device information and saves it as unconfirmed data.

    Args:
        token (Token): The authentication token containing user and activity information.
        id (int): The ID of the device to change the status for.
        db (Session): The database session.
        current_concierge (int): The current concierge ID, used for authorization.

    Returns:
        DeviceOrDetailResponse: The updated device object or the information that the
        device was removed from unapproved data.

    Raises:
        HTTPException: If the activity associated with the token does not exist.
        HTTPException: If an error occurs while updating the device status.
    """
    unapproved_dev_service = deviceService.UnapprovedDeviceService(db)
    dev_service = deviceService.DeviceService(db)
    unapproved_dev_service = deviceService.UnapprovedDeviceService(db)
    activity_service = activityService.ActivityService(db)

    activity = activity_service.get_activity_token(token)

    if unapproved_dev_service.delete_if_rescaned(id):
        return DetailMessage(detail="Device removed from unapproved data.")

    device = dev_service.get_dev_id(id)

    if not device.is_taken:
        new_data = {
            "is_taken": True,
            "last_taken": datetime.datetime.now(datetime.timezone.utc),
            "last_owner_id": activity.user_id
        }
    else:
        new_data = {
            "is_taken": False,
            "last_returned": datetime.datetime.now(datetime.timezone.utc)
        }
    unapproved_dev_service.create_unapproved(id, activity.id)

    return unapproved_dev_service.update_device_status(id, new_data)
