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


@router.get("/unapproved/{session_id}",
            response_model=List[schemas.DeviceUnapproved],
            responses={
                200: {"description": "List with details of all unapproved devices based on a specific session ID.", },
                401: {"description": "Invalid token or the credentials can not be validated"},
                403: {"description": "You are logged out or you cannot perform the operation with your role"},
                404: {"description": "No unapproved devices found for this session"}
                })
def get_unapproved_device_session(session_id: int,
                                  current_concierge=Depends(oauth2.get_current_concierge),
                                  db: Session = Depends(database.get_db)) -> List[schemas.DeviceUnapproved]:
    """
    Retrieve List with details of all unapproved devices based on a specific session ID.

    This endpoint allows the logged-in concierge to access information about a devices
    that were modified during a given session and have not been approved yet.
    """
    unapproved_dev_service = deviceService.UnapprovedDeviceService(db)
    return unapproved_dev_service.get_unapproved_dev_session(session_id)


@router.get("/unapproved", response_model=List[schemas.DeviceUnapproved])
def get_all_unapproved(current_concierge=Depends(oauth2.get_current_concierge),
                       db: Session = Depends(database.get_db)) -> List[schemas.DeviceUnapproved]:
    """
    Retrieve all unapproved devices stored in the system.

    This endpoint returns a list of all unapproved devices.s
    """
    unapproved_dev_service = deviceService.UnapprovedDeviceService(db)
    return unapproved_dev_service.get_unapproved_dev_all()


@router.get("/", response_model=List[schemas.DeviceOut])
def get_devices_filtered(current_concierge=Depends(oauth2.get_current_concierge),
                         dev_type: str = "",
                         dev_version: str = "",
                         room_number: str ="",
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
    return dev_service.get_all_devs(dev_type, dev_version, room_number)


@router.get("/{dev_id}", response_model=schemas.DeviceOut)
def get_dev_id(dev_id: int,
                 current_concierge=Depends(oauth2.get_current_concierge),
                 db: Session = Depends(database.get_db)) -> schemas.DeviceOut:
    """
    Retrieve a device by its unique device code.

    This endpoint retrieves a device from the database using the device's unique code.
    """
    dev_service = deviceService.DeviceService(db)
    return dev_service.get_dev_id(dev_id)


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


@router.post("/change-status", response_model=schemas.DeviceOperationOrDetailResponse)
def change_status(
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

    device = dev_service.get_dev_id(request.device_id)
    if unapproved_dev_service.delete_if_rescanned(request.device_id, request.issue_return_session_id):
        return schemas.DetailMessage(detail="Device removed from unapproved data.")

    session = session_service.get_session_id(request.issue_return_session_id)

    entitled = permission_service.check_if_permitted(session.user_id, device.room.id, device.is_taken, force = request.force)
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

    new_dev_data["device_id"] = request.device_id
    new_dev_data["issue_return_session_id"] = session.id

    operation_type = (models.OperationType.return_dev if device.is_taken else models.OperationType.issue_dev)
    operation_data = {
        "device_id": request.device_id,
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


@router.get("/users/{user_id}", response_model=List[schemas.DeviceOut])
def get_devs_owned_by_user(user_id: int,
                           current_concierge=Depends(oauth2.get_current_concierge),
                           db: Session = Depends(database.get_db)) -> List[schemas.DeviceOut]:
    """
    Retrieve a device by its unique device code.

    This endpoint retrieves a device from the database using the device's unique code.
    """
    dev_service = deviceService.DeviceService(db)
    return dev_service.get_dev_owned_by_user(user_id)
