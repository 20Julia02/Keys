from fastapi import HTTPException, status, Depends, APIRouter, Response, Query
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
    response: Response,
    request: schemas.ChangeStatus,
    db: Session = Depends(database.get_db),
    current_concierge: User = Depends(oauth2.get_current_concierge),
) -> schemas.DevOperationOrDetailResponse:
    """
    Changes the status of a device based on the session, user permissions, and an optional force flag.

    Functionality:
    - Determines the next operation type (`pobranie` or `zwrot`) based on the last approved operation for the device.
    - Validates user permissions to ensure the user is entitled to perform the operation:
        - If the user does not have permission, the `force` flag is not set, and the next operation type is `pobranie`, 
        the operation is denied with an appropriate error message.
    - Handles rescanning of the device within the current session:
        - If the detected operation type is `pobranie` (retrieval), rescanning is treated as a `zwrot` (return). In this case:
            - Even if the user does not have permission and the `force` flag is not set, 
            no error is raised and the unapproved operation is removed.
        - If the detected operation type is `zwrot` (return), rescanning is treated as a `pobranie` (retrieval). In this case:
            - If the user does not have permission and the `force` flag is not set, an error is raised. 
            Otherwise, the unapproved operation is removed.
    - If the operation is not a repeated scan, the user is entitled, or the `force` flag is set, 
    a new unapproved operation is created for further validation.

    The operation ensures that the requesting user is authenticated and updates their access token.
    """
    logger.info(f"POST request to change device status")
    oauth2.set_access_token_cookie(response, current_concierge.id, current_concierge.role.value, db)
    device = mdevice.Device.get_dev_by_code(db, request.device_code)
    session = moperation.UserSession.get_session_id(db, request.session_id)

    last_operation = moperation.DeviceOperation.get_last_dev_operation_or_none(db,
                                                                               device.id)
    entitled = mpermission.Permission.check_if_permitted(
        db,
        session.user_id,
        device.room_id,
    )

    operation_type = "zwrot" if last_operation and last_operation.operation_type == "pobranie" else "pobranie"
    if not entitled and not request.force:
        if operation_type == "pobranie":
            if moperation.UnapprovedOperation.delete_if_rescanned(db, device.id, request.session_id):
                return schemas.DetailMessage(detail="Operation removed.")
            logger.warning(
                f"User with ID {session.user_id} has no permission to perform the operation")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="User has no permission to perform the operation")
        elif operation_type == "zwrot":
            if moperation.UnapprovedOperation.check_if_rescanned(db, device.id, request.session_id):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="User has no permission to perform the operation")

    elif moperation.UnapprovedOperation.delete_if_rescanned(db, device.id, request.session_id):
                return schemas.DetailMessage(detail="Operation removed.")
    
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
                           response: Response,
                           current_concierge: User = Depends(
                               oauth2.get_current_concierge),
                           db: Session = Depends(database.get_db)) -> Sequence[schemas.DevOperationOut]:
    """
    Retrieve a list of devices owned by a specific user.

    This endpoint fetches the devices associated with a given user ID.

    The operation ensures that the requesting user is authenticated and updates their access token.
    """
    logger.info(
        f"GET request to retrieve the device owned by user: {user_id}")
    oauth2.set_access_token_cookie(response, current_concierge.id, current_concierge.role.value, db)
    return moperation.DeviceOperation.get_last_operation_user_id(db, user_id)


@router.get("/unapproved", response_model=Sequence[schemas.DevOperationOut])
def get_unapproved_operations(response: Response,
                              session_id: Optional[int] = None,
                              operation_type: Optional[Literal["pobranie",
                                                               "zwrot"]] = Query(
        None, description="Filter operations by type. Possible values: 'pobranie', 'zwrot'."
    ),
                              current_concierge: User = Depends(
                                  oauth2.get_current_concierge),
                              db: Session = Depends(database.get_db)) -> Sequence[schemas.DevOperationOut]:
    """
    Retrieve a list of unapproved operations.

    This endpoint fetches operations that have not yet been approved, optionally filtered
    by session ID and operation type. Supported operation types include "pobranie" (issue)
    and "zwrot" (return).
    
    The operation ensures that the requesting user is authenticated and updates their access token.
    """
    logger.info(
        f"GET request to retrieve the unapproved operations with operation_type: {operation_type}")
    oauth2.set_access_token_cookie(response, current_concierge.id, current_concierge.role.value, db)
    return moperation.UnapprovedOperation.get_unapproved_filtered(db, session_id, operation_type)


@router.get("/", response_model=Sequence[schemas.DevOperationOut])
def get_operations_filtered(response: Response,
                            session_id: Optional[int] = None,
                            current_concierge: User = Depends(
        oauth2.get_current_concierge),
        db: Session = Depends(database.get_db)) -> Sequence[schemas.DevOperationOut]:
    """
    Retrieve all operations with optional filtering by session ID.

    This endpoint fetches all operations from the database. If a session ID is provided,
    only operations linked to that session are returned.

    The operation ensures that the requesting user is authenticated and updates their access token.
    """
    logger.info(
        f"GET request to retrieve the operations with session ID: {session_id}")
    oauth2.set_access_token_cookie(response, current_concierge.id, current_concierge.role.value, db)
    return moperation.DeviceOperation.get_all_operations(db, session_id)


@router.get("/{operation_id}", response_model=schemas.DevOperationOut)
def get_operation_id(response: Response,
                     operation_id: int,
                     current_concierge: User = Depends(
                         oauth2.get_current_concierge),
                     db: Session = Depends(database.get_db)) -> schemas.DevOperationOut:
    """
    Retrieve details of a specific operation by its unique ID.

    This endpoint fetches detailed information about a single operation, identified
    by its unique ID.

    The operation ensures that the requesting user is authenticated and updates their access token.
    """
    logger.info(
        f"GET request to retrieve the operations by ID: {operation_id}")
    oauth2.set_access_token_cookie(response, current_concierge.id, current_concierge.role.value, db)
    return moperation.DeviceOperation.get_operation_id(db, operation_id)


@router.get("/device/{device_id}", response_model=schemas.DevOperationOut | None)
def get_last_dev_operation_or_none(response: Response,
                                   device_id: int,
                                   current_concierge: User = Depends(
                                       oauth2.get_current_concierge),
                                   db: Session = Depends(database.get_db)) -> schemas.DevOperationOut | None:
    """
    Retrieve the most recent operation for a specific device.

    This endpoint fetches the latest operation associated with a given device ID.
    If no operations exist for the device, the response will be `None`.

    The operation ensures that the requesting user is authenticated and updates their access token.
    """
    logger.info(
        f"GET request to retrieve the operations for device with ID: {device_id}")
    oauth2.set_access_token_cookie(response, current_concierge.id, current_concierge.role.value, db)
    return moperation.DeviceOperation.get_last_dev_operation_or_none(db, device_id)
