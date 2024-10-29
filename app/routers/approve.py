from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from app import database, oauth2, schemas
from app.services import securityService
import app.models.operation as moperation
from app.models.user import User
from typing import Sequence
from fastapi import Path

router = APIRouter(
    tags=['Approve']
)


@router.post("/approve/login/session/{session_id}",
             response_model=Sequence[schemas.DeviceOperationOut],
             responses={
                 200: {
                     "description": "Session successfully approved.",
                     "content": {
                         "application/json": {
                             "example": [
                                 {
                                     "id": 1,
                                     "device": {
                                         "id": 1,
                                         "code": "ABC123",
                                         "dev_type": "Tablet",
                                         "dev_version": "v2.0",
                                         "room": {
                                             "id": 101,
                                             "number": "42A"
                                         }
                                     },
                                     "session": {
                                         "id": 1,
                                         "user_id": 5,
                                         "concierge_id": 2,
                                         "start_time": "2023-10-12T13:18:04.071Z",
                                         "status": "w trakcie"
                                     },
                                     "operation_type": "activate_device",
                                     "entitled": True,
                                     "timestamp": "2023-10-12T13:18:04.071Z"
                                 }
                             ]
                         }
                     },
                 },
                 403: {
                     "description": "Authentication failed due to incorrect login credentials.",
                     "content": {
                         "application/json": {
                             "example": {
                                 "invalid_card_code": {
                                     "detail": "Invalid credential"
                                 },
                                 "not_entitled": {
                                     "detail": "You cannot perform this operation without the concierge role"
                                 }
                             }
                         }
                     }
                 },
                 404: {
                     "description": "Session not found or no unapproved operations for the session.",
                     "content": {
                         "application/json": {
                             "example": {
                                 "session_not_found": {
                                     "detail": "Session not found"
                                 },
                                 "no_operations_found": {
                                     "detail": "No unapproved operations found for this session"
                                 }
                             }
                         }
                     }
                 },
                 422: {
                     "description": "Validation Error: Invalid input or malformed data.",
                     "content": {
                         "application/json": {
                             "example": {
                                 "detail": [
                                     {
                                         "loc": ["path", "session_id"],
                                         "msg": "Session ID must be an integer",
                                         "type": "type_error.integer"
                                     }
                                 ]
                             }
                         }
                     }
                 },
                 500: {
                     "description": "Internal server error occurred during the operation transfer process..",
                     "content": {
                         "application/json": {
                             "example": {
                                 "detail": "Error during operation transfer"
                             }
                         }
                     }
                 },
             }
             )
def approve_session_login(session_id: int = Path(description="Unique identifier of the session that contains operations awaiting approval."),
                          db: Session = Depends(database.get_db),
                          concierge_credentials: OAuth2PasswordRequestForm = Depends(),
                          current_concierge: User = Depends(oauth2.get_current_concierge)) -> Sequence[schemas.DeviceOperationOut]:
    """
    Approve a session and its associated operations using login credentials for authentication.

    This endpoint finalizes an session, allowing a concierge to approve operations
    which modifies devices during the session. The concierge must authenticate via login credentials before approval.
    Once approved, the operations are transferred from the unapproved state to the approved operations data.
    """
    auth_service = securityService.AuthorizationService(db)
    auth_service.authenticate_user_login(
        concierge_credentials.username, concierge_credentials.password, "concierge")
    moperation.UserSession.end_session(db, session_id)
    operations = moperation.UnapprovedOperation.create_operation_from_unapproved(
        db, session_id)
    return operations


@router.post("/approve/card/session/{session_id}",
             response_model=Sequence[schemas.DeviceOperationOut],
             responses={
                 200: {
                     "description": "Session successfully approved.",
                     "content": {
                         "application/json": {
                             "example": [
                                 {
                                     "id": 1,
                                     "device": {
                                         "id": 1,
                                         "code": "ABC123",
                                         "dev_type": "Tablet",
                                         "dev_version": "v2.0",
                                         "room": {
                                             "id": 101,
                                             "number": "42A"
                                         }
                                     },
                                     "session": {
                                         "id": 1,
                                         "user_id": 5,
                                         "concierge_id": 2,
                                         "start_time": "2023-10-12T13:18:04.071Z",
                                         "status": "w trakcie"
                                     },
                                     "operation_type": "activate_device",
                                     "entitled": True,
                                     "timestamp": "2023-10-12T13:18:04.071Z"
                                 }
                             ]
                         }
                     },
                 },
                 403: {
                     "description": "Authentication failed due to incorrect login credentials.",
                     "content": {
                         "application/json": {
                             "example": {
                                 "invalid_card_code": {
                                     "detail": "Invalid credential"
                                 },
                                 "not_entitled": {
                                     "detail": "You cannot perform this operation without the concierge role"
                                 },
                                 "session_already_approved": {
                                     "detail": "Session has been allready ended with status potwierdzona"
                                 }
                             }
                         }
                     }
                 },
                 404: {
                     "description": "Session not found or no unapproved operations for the session.",
                     "content": {
                         "application/json": {
                             "example": {
                                 "session_not_found": {
                                     "detail": "Session not found"
                                 },
                                 "no_operations_found": {
                                     "detail": "No unapproved operations found for this session"
                                 }
                             }
                         }
                     }
                 },
                 422: {
                     "description": "Validation Error: Invalid input or malformed data.",
                     "content": {
                         "application/json": {
                             "example": {
                                 "detail": [
                                     {
                                         "loc": ["path", "session_id"],
                                         "msg": "Session ID must be an integer",
                                         "type": "type_error.integer"
                                     }
                                 ]
                             }
                         }
                     }
                 },
                 500: {
                     "description": "Internal server error occurred during the operation transfer process..",
                     "content": {
                         "application/json": {
                             "example": {
                                 "detail": "Error during operation transfer"
                             }
                         }
                     }
                 },
             }
             )
def approve_session_card(
    card_data: schemas.CardId,
    session_id: int = Path(
        description="Unique identifier of the session that contains operations awaiting approval."),
    db: Session = Depends(database.get_db),
    current_concierge: User = Depends(oauth2.get_current_concierge)
) -> Sequence[schemas.DeviceOperationOut]:
    """
    Approve a session and its associated operations using card code.

    This endpoint finalizes an session, allowing a concierge to approve operations
    which modifies devices during the session. The concierge must authenticate via card before approval.
    Once approved, the operations are transferred from the unapproved state to the approved operations data.
    """
    auth_service = securityService.AuthorizationService(db)
    auth_service.authenticate_user_card(card_data, "concierge")

    moperation.UserSession.end_session(db, session_id)

    operations = moperation.UnapprovedOperation.create_operation_from_unapproved(
        db, session_id)

    return operations
