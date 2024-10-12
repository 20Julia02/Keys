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


@router.get("/", response_model=List[schemas.DeviceOutNote])
def get_devices_filtered(current_concierge=Depends(oauth2.get_current_concierge),
                         dev_type: str = "",
                         dev_version: str = "",
                         room_number: str ="",
                         db: Session = Depends(database.get_db)) -> List[schemas.DeviceOutNote]:
    """
    Retrieve all devices from the database, optionally filtered by type or dev_version.

    This endpoint retrieves a list of devices from the database. Optionally,
    the list can be filtered by device type and dev_version if these parameters are provided.

    Args:
        current_concierge: The currently authenticated concierge (used for authorization).
        dev_type (str): Optional filter for device type.
        dev_version (str): Optional filter for device dev_version.
        db (Session): The active database session.

    Returns:
        List[schemas.DeviceOut]: A list of devices that match the optional filters, if any.

    Raises:
        HTTPException: If no devices are found or there is a database error.
    """
    dev_service = deviceService.DeviceService(db)
    return dev_service.get_devs_filtered(dev_type, dev_version, room_number)


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


@router.post("/change-status", response_model=schemas.DeviceOperationOrDetailResponse)
def change_status(
    request: schemas.ChangeStatus,
    db: Session = Depends(database.get_db),
    current_concierge: int = Depends(oauth2.get_current_concierge),
) -> schemas.DeviceOperationOrDetailResponse:
    """
    Change the status of the device based on session id, permissions, and optional force flag.

    - If the device has already been added as unapproved in the current session, remove the unapproved operation.
    - Otherwise, check user permissions and create a new unapproved operation (issue or return).
    """
    dev_service = deviceService.DeviceService(db)
    operation_service = operationService.DeviceOperationService(db)
    unapproved_service = operationService.UnapprovedOperationService(db)
    session_service = sessionService.SessionService(db)
    permission_service = permissionService.PermissionService(db)

    device = dev_service.get_dev_id(request.device_id)
    session = session_service.get_session_id(request.session_id)

    if unapproved_service.delete_if_rescanned(request.device_id, request.session_id):
        return schemas.DetailMessage(detail="Operation removed.")
    last_operation = operation_service.get_last_dev_operation_or_none(device.id)
    entitled = permission_service.check_if_permitted(
        session.user_id, 
        device.room_id,
        last_operation.operation_type if last_operation else None,
        request.force
    )
    operation_type = "return_dev" if last_operation and last_operation.operation_type == "issue_dev" else "issue_dev"
    operation = unapproved_service.create_unapproved_operation({
        "device_id": request.device_id,
        "session_id": session.id,
        "entitled": entitled,
        "operation_type": operation_type
    })

    return operation


@router.get("/users/{user_id}", response_model=List[schemas.DeviceOperationOut])
def get_devs_owned_by_user(user_id: int,
                           current_concierge=Depends(oauth2.get_current_concierge),
                           db: Session = Depends(database.get_db)) -> List[schemas.DeviceOut]:
    """
    Retrieve a device by its unique device code.

    This endpoint retrieves a device from the database using the device's unique code.
    """
    dev_service = deviceService.DeviceService(db)
    return dev_service.get_devs_owned_by_user(user_id)
