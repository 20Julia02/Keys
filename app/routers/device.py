import datetime
from fastapi import status, Depends, APIRouter
from typing import List
from app.schemas import ChangeStatus, DeviceCreate, DeviceOut, DetailMessage, DeviceOrDetailResponse, Operation
from app import database, oauth2, models
from app.services import deviceService, securityService, activityService, operationService, permissionService
from sqlalchemy.orm import Session


router = APIRouter(
    prefix="/devices",
    tags=['Devices']
)


@router.get("/", response_model=List[DeviceOut])
def get_all_devices(current_concierge=Depends(oauth2.get_current_concierge),
                    dev_type: str = "",
                    dev_version: str = "",
                    db: Session = Depends(database.get_db)) -> List[DeviceOut]:
    """
    Retrieve all devices from the database, optionally filtered by type or version.

    This endpoint retrieves a list of devices from the database. Optionally, 
    the list can be filtered by device type and version if these parameters are provided.
    
    Args:
        current_concierge: The currently authenticated concierge (used for authorization).
        dev_type (str): Optional filter for device type.
        dev_version (str): Optional filter for device version.
        db (Session): The active database session.

    Returns:
        List[DeviceOut]: A list of devices that match the optional filters, if any.
    
    Raises:
        HTTPException: If no devices are found or there is a database error.
    """
    dev_service = deviceService.DeviceService(db)
    return dev_service.get_all_devs(dev_type, dev_version)


@router.get("/{dev_code}", response_model=DeviceOut)
def get_dev_code(dev_code: str,
                 current_concierge=Depends(oauth2.get_current_concierge),
                 db: Session = Depends(database.get_db)) -> DeviceOut:
    """
    Retrieve a device by its unique device code.

    This endpoint retrieves a device from the database using the device's unique code.

    Args:
        dev_code (str): The unique code of the device.
        current_concierge: The currently authenticated concierge (used for authorization).
        db (Session): The active database session.

    Returns:
        DeviceOut: The device that matches the provided code.

    Raises:
        HTTPException: If the device with the given code is not found.
    """
    dev_service = deviceService.DeviceService(db)
    return dev_service.get_dev_code(dev_code)


@router.post("/", response_model=DeviceOut, status_code=status.HTTP_201_CREATED)
def create_device(device: DeviceCreate,
                  db: Session = Depends(database.get_db),
                  current_concierge=Depends(oauth2.get_current_concierge)) -> DeviceOut:
    """
    Create a new device in the database.

    This endpoint allows concierge to create a new device by providing the necessary 
    data. Only users with the 'admin' role are permitted to create devices.

    Args:
        device (DeviceCreate): The data required to create the new device.
        db (Session): The active database session.
        current_concierge: The currently authenticated concierge (used for authorization).

    Returns:
        DeviceOut: The newly created device.

    Raises:
        HTTPException: If the user is not authorized to create a device.
    """
    auth_service = securityService.AuthorizationService(db)
    auth_service.check_if_entitled("admin", current_concierge)
    dev_service = deviceService.DeviceService(db)
    return dev_service.create_dev(device)

# todo zmiana statusu unauthorized

@router.post("/change-status/{dev_code}", response_model=DeviceOrDetailResponse)
def change_status(
    dev_code: str,
    request: ChangeStatus,
    db: Session = Depends(database.get_db),
    current_concierge: int = Depends(oauth2.get_current_concierge),
) -> DeviceOrDetailResponse:
    """
   changes the status of the device based on the given activity id and whether to force the operation 
   without permissions (if the parameter force == true the operation will be performed even 
   without the corresponding user rights)

    If the device has already been approved, it removes the device 
    from unapproved data. 
    
    Otherwise, it checks user permissions, updates the device information and saves it as 
    unconfirmed data. The status change reflects whether the device has been issued or returned.

    Args:
        dev_id (int): The ID of the device whose status is being changed.
        request (ChangeStatus): The request object containing activity ID and other details.
        db (Session): The active database session.
        current_concierge (int): The current concierge ID, used for authorization.

    Returns:
        DeviceOrDetailResponse: The updated device object or a message confirming the 
        device's removal from unapproved data.
    
    Raises:
        HTTPException: If the associated activity does not exist or there is an error 
        updating the device status.
    """
    unapproved_dev_service = deviceService.UnapprovedDeviceService(db)
    dev_service = deviceService.DeviceService(db)
    activity_service = activityService.ActivityService(db)
    operation_service = operationService.OperationService(db)
    permission_service = permissionService.PermissionService(db)

    dev_unapproved = db.query(models.DevicesUnapproved).filter(models.DevicesUnapproved.device_code == dev_code, 
                                                       models.DevicesUnapproved.activity_id == request.activity_id).first()
    if dev_unapproved:
        db.delete(dev_unapproved)
        db.commit()
        return DetailMessage(detail="Device removed from unapproved data.")
    
    activity = activity_service.get_activity_id(request.activity_id)
    
    device = dev_service.get_dev_code(dev_code)
    entitled = permission_service.check_if_permitted(activity.user_id, device.room.id, request.force)

    if not device.is_taken:  
        operation_type = models.OperationType.issue_dev.value

        new_dev_data = {
            "is_taken": True,
            "last_taken": datetime.datetime.now(datetime.timezone.utc),
            "last_owner_id": activity.user_id,
        }

    else:
        operation_type = models.OperationType.return_dev.value

        new_dev_data = {
            "is_taken": False,
            "last_returned": datetime.datetime.now(datetime.timezone.utc)
        }

    operation_service.create_operation(dev_code, activity.id, entitled, operation_type)
    
    return unapproved_dev_service.create_unapproved(dev_code, activity.id, new_dev_data)
