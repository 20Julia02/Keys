import datetime
from zoneinfo import ZoneInfo
from fastapi import status, Depends, APIRouter, HTTPException
from typing import List
from app import database, oauth2, models, schemas
from app.services import deviceService, securityService, sessionService, operationService, permissionService
from sqlalchemy.orm import Session


router = APIRouter(
    prefix="/devices",
    tags=['Devices']    
)


@router.get("/", response_model=List[schemas.DeviceOut])
def get_all_devices(current_concierge=Depends(oauth2.get_current_concierge),
                    dev_type: str = "",
                    dev_version: str = "",
                    db: Session = Depends(database.get_db)) -> List[schemas.DeviceOut]:
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
        List[schemas.DeviceOut]: A list of devices that match the optional filters, if any.
    
    Raises:
        HTTPException: If no devices are found or there is a database error.
    """
    dev_service = deviceService.DeviceService(db)
    return dev_service.get_all_devs(dev_type, dev_version)


@router.get("/{dev_code}", response_model=schemas.DeviceOut)
def get_dev_code(dev_code: str,
                 current_concierge=Depends(oauth2.get_current_concierge),
                 db: Session = Depends(database.get_db)) -> schemas.DeviceOut:
    """
    Retrieve a device by its unique device code.

    This endpoint retrieves a device from the database using the device's unique code.
    """
    dev_service = deviceService.DeviceService(db)
    return dev_service.get_dev_code(dev_code)


@router.post("/", response_model=schemas.DeviceOut, status_code=status.HTTP_201_CREATED)
def create_device(device: schemas.DeviceCreate,
                  db: Session = Depends(database.get_db),
                  current_concierge=Depends(oauth2.get_current_concierge)) -> schemas.DeviceOut:
    """
    Create a new device in the database.

    This endpoint allows concierge to create a new device by providing the necessary 
    data. Only users with the 'admin' role are permitted to create devices.
    """
    auth_service = securityService.AuthorizationService(db)
    auth_service.check_if_entitled("admin", current_concierge)
    dev_service = deviceService.DeviceService(db)
    return dev_service.create_dev(device)

# todo zmiana statusu unauthorized

@router.post("/change-status/{dev_code}", response_model=schemas.DeviceOperationOrDetailResponse)
def change_status(
    dev_code: str,
    request: schemas.ChangeStatus,
    db: Session = Depends(database.get_db),
    current_concierge: int = Depends(oauth2.get_current_concierge),
) -> schemas.DeviceOperationOrDetailResponse:
    """
    changes the status of the device with given code based on the given session id and whether to force the operation 
    without permissions (if the parameter force == true the operation will be performed even 
    without the corresponding user rights)

    If the device has already been added to the unapproved data in the current session (with givenn session id),
    it removes the device from unapproved data. 
    
    Otherwise, it checks user permissions and creates the operation containing all information about the status change 
    performed. Then, it updates the device information and saves it as unconfirmed data.
    The new device data depends on whether the device has been issued or returned.
    """
    unapproved_dev_service = deviceService.UnapprovedDeviceService(db)
    dev_service = deviceService.DeviceService(db)
    operation_service = operationService.DeviceOperationService(db)
    session_service = sessionService.SessionService(db)
    permission_service = permissionService.PermissionService(db)

    dev_unapproved = db.query(models.DeviceUnapproved).filter(models.DeviceUnapproved.device_code == dev_code, 
                                                               models.DeviceUnapproved.issue_return_session_id == request.issue_return_session_id).first()
    if dev_unapproved:
        db.delete(dev_unapproved)
        db.commit()
        return schemas.DetailMessage(detail="Device removed from unapproved data.")
    
    session = session_service.get_session_id(request.issue_return_session_id)
    
    device = dev_service.get_dev_code(dev_code)
    entitled = permission_service.check_if_permitted(session.user_id, device.room.id, request.force)


    if not device.is_taken:  
        new_dev_data = {
            "is_taken": True,
            "last_taken": datetime.datetime.now(ZoneInfo("Europe/Warsaw")),
            "last_owner_id": session.user_id,
        }

    else:
        new_dev_data = {
            "is_taken": False,
            "last_returned": datetime.datetime.now(ZoneInfo("Europe/Warsaw"))
        }
    
    new_dev_data["device_code"] = dev_code
    new_dev_data["issue_return_session_id"] = session.id

    operation_type = (models.OperationType.return_dev if device.is_taken else models.OperationType.issue_dev)
    operation_data = {
        "device_code": dev_code,
        "issue_return_session_id": session.id,
        "operation_type": operation_type,
        "entitled": entitled
    }
    try:
        
        unapproved_dev_service.create_unapproved(new_dev_data, False)
        operation = operation_service.create_operation(operation_data, False)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error occurred while processing device status change: {str(e)}"
        )
    return operation