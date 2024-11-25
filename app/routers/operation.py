from fastapi import HTTPException, status, Depends, APIRouter
from typing import Optional, Sequence, Literal
from app import database, oauth2, schemas
import app.models.device as mdevice
from sqlalchemy.orm import Session
import app.models.operation as moperation
import app.models.permission as mpermission
from app.models.user import User
from app.config import logger


router = APIRouter(
    prefix="/operations",
    tags=['Operaions']
)


@router.post("/change-status", response_model=schemas.DevOperationOrDetailResponse)
def change_status(
    request: schemas.ChangeStatus,
    db: Session = Depends(database.get_db),
    current_concierge: int = Depends(oauth2.get_current_concierge),
) -> schemas.DevOperationOrDetailResponse:
    """
    Change the status of the device based on session id, permissions, and optional force flag.

    - If the device has already been added as unapproved in the current session, remove the unapproved operation.
    - Otherwise, check user permissions and create a new unapproved operation (issue or return).
    """
    logger.info(f"POST request to change device status: {request}")

    device = mdevice.Device.get_dev_by_code(db, request.device_code)
    session = moperation.UserSession.get_session_id(db, request.session_id)

    if moperation.UnapprovedOperation.delete_if_rescanned(db, device.id, request.session_id):
        return schemas.DetailMessage(detail="Operation removed.")
    last_operation = moperation.DeviceOperation.get_last_dev_operation_or_none(db,
                                                                               device.id)
    entitled = mpermission.Permission.check_if_permitted(
        db,
        session.user_id,
        device.room_id,
    )
    operation_type = "zwrot" if last_operation and last_operation.operation_type == "pobranie" else "pobranie"
    if entitled == False and request.force == False and operation_type == "pobranie":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"User with ID {session.user_id} has no permission to perform the operation")
    operation_data = schemas.DevOperation(
        device_id=device.id,
        session_id=session.id,
        entitled=entitled,
        operation_type=operation_type
    )
    operation = moperation.UnapprovedOperation.create_unapproved_operation(
        db, operation_data)

    return operation


@router.get("/users/{user_id}", response_model=Sequence[schemas.DevOperationOut])
def get_devs_owned_by_user(user_id: int,
                           current_concierge: User = Depends(
                               oauth2.get_current_concierge),
                           db: Session = Depends(database.get_db)) -> Sequence[schemas.DevOperationOut]:
    logger.info(
        f"GET request to retrieve the device owned by user: {user_id}")

    return moperation.DeviceOperation.get_last_operation_user_id(db, user_id)


@router.get("/unapproved", response_model=Sequence[schemas.DevOperationOut])
def get_unapproved_operations(session_id: Optional[int] = None,
                              operation_type: Optional[Literal["pobranie",
                                                               "zwrot"]] = None,
                              current_concierge: User = Depends(
                                  oauth2.get_current_concierge),
                              db: Session = Depends(database.get_db)) -> Sequence[schemas.DevOperationOut]:
    return moperation.UnapprovedOperation.get_unapproved_filtered(db, session_id, operation_type)


@router.get("/", response_model=Sequence[schemas.DevOperationOut])
def get_operations_filtered(session_id: Optional[int] = None,
                            current_concierge: User = Depends(
        oauth2.get_current_concierge),
        db: Session = Depends(database.get_db)) -> Sequence[schemas.DevOperationOut]:

    return moperation.DeviceOperation.get_all_operations(db, session_id)


@router.get("/{operation_id}", response_model=schemas.DevOperationOut)
def get_operation_id(operation_id: int,
                     current_concierge: User = Depends(
                         oauth2.get_current_concierge),
                     db: Session = Depends(database.get_db)) -> schemas.DevOperationOut:

    return moperation.DeviceOperation.get_operation_id(db, operation_id)


@router.get("/device/{device_id}", response_model=schemas.DevOperationOut | None)
def get_last_dev_operation_or_none(device_id: int,
                                   current_concierge: User = Depends(
                                       oauth2.get_current_concierge),
                                   db: Session = Depends(database.get_db)) -> schemas.DevOperationOut | None:

    return moperation.DeviceOperation.get_last_dev_operation_or_none(db, device_id)
