from fastapi import status, Depends, APIRouter
from typing import List, Optional
from app import database, oauth2, schemas
import app.models.device as mdevice
from app.services import securityService, sessionService, operationService, permissionService
from sqlalchemy.orm import Session
import app.models.operation as moperation


router = APIRouter(
    prefix="/devices",
    tags=['Devices']
)


@router.get("/", response_model=List[schemas.DeviceOutWithNote])
def get_devices_filtered(current_concierge=Depends(oauth2.get_current_concierge),
                         dev_type: Optional[str] = None,
                         dev_version: Optional[str] = None,
                         room_number: Optional[str] = None,
                         db: Session = Depends(database.get_db)) -> List[schemas.DeviceOutWithNote]:
    """
    Retrieve all devices from the database, optionally filtered by type or dev_version.

    This endpoint retrieves a list of devices from the database. Optionally,
    the list can be filtered by device type and dev_version if these parameters are provided.
    """
    return mdevice.Device.get_device_with_details(db, dev_type, dev_version, room_number)


@router.get("/code/{dev_code}", response_model=schemas.DeviceOut)
def get_dev_code(dev_code: str,
                 current_concierge=Depends(oauth2.get_current_concierge),
                 db: Session = Depends(database.get_db)) -> schemas.DeviceOut:
    """
    Retrieve a device by its unique device code.

    This endpoint retrieves a device from the database using the device's unique code.
    """
    return mdevice.Device.get_by_code(db, dev_code)


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
    return  mdevice.Device.create(db, device)


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
    operation_service = operationService.DeviceOperationService(db)
    unapproved_service = operationService.UnapprovedOperationService(db)
    session_service = sessionService.SessionService(db)
    permission_service = permissionService.PermissionService(db)

    device = mdevice.Device.get_by_id(db, request.device_id)
    session = session_service.get_session_id(request.session_id)

    if unapproved_service.delete_if_rescanned(request.device_id, request.session_id):
        return schemas.DetailMessage(detail="Operation removed.")
    last_operation = operation_service.get_last_dev_operation_or_none(
        device.id)

    entitled = permission_service.check_if_permitted(
        session.user_id,
        device.room_id,
        last_operation.operation_type if last_operation else None,
        request.force
    )
    operation_type = "zwrot" if last_operation and last_operation.operation_type == "pobranie" else "pobranie"
    operation = unapproved_service.create_unapproved_operation({
        "device_id": request.device_id,
        "session_id": session.id,
        "entitled": entitled,
        "operation_type": operation_type
    })

    return operation


@router.get("/users/{user_id}", response_model=List[schemas.DeviceOperationOut])
def get_devs_owned_by_user(user_id: int,
                           current_concierge=Depends(
                               oauth2.get_current_concierge),
                           db: Session = Depends(database.get_db)) -> List[schemas.DeviceOperationOut]:
    """
    Retrieve a device by its unique device code.

    This endpoint retrieves a device from the database using the device's unique code.
    """
    return moperation.DeviceOperation.get_owned_by_user(db, user_id)
