from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from app import database, oauth2, schemas
from app.services import operationService, securityService, sessionService, deviceService
from typing import List

router = APIRouter(
    tags=['Approve']
)

@router.post("/approve/login/session/{session_id}", response_model=List[schemas.DeviceOperationOut])
def approve_session_login(session_id: int,
                          db: Session = Depends(database.get_db),
                          concierge_credentials: OAuth2PasswordRequestForm = Depends(),
                          current_concierge=Depends(oauth2.get_current_concierge)) -> List[schemas.DeviceOperationOut]:
    """
    Approve a session and its associated operations using login credentials for authentication.

    This endpoint finalizes an session, allowing a concierge to approve devices
    modified during the session. The concierge must authenticate via login credentials before approval.
    Once approved, the devices are transferred from the unapproved state to the approved device data.
    """
    auth_service = securityService.AuthorizationService(db)
    unapproved_operation_service = operationService.UnapprovedOperationService(db)
    session_service = sessionService.SessionService(db)
    auth_service.authenticate_user_login(concierge_credentials.username, concierge_credentials.password, "concierge")
    session_service.end_session(session_id)
    operations = unapproved_operation_service.create_operation_from_unappproved(session_id)
    return operations


@router.post("/approve/card/session/{session_id}", response_model=List[schemas.DeviceOperationOut])
def approve_session_card(session_id,
                         card_data: schemas.CardLogin,
                         db: Session = Depends(database.get_db),
                         current_concierge=Depends(oauth2.get_current_concierge)
                         ) -> JSONResponse:
    """
    Approve an session and its associated devices using card credentials for authentication.

    This endpoint finalizes an session, allowing a concierge to approve devices
    used during the session. The concierge must authenticate using card-based credentials (an ID card).
    Once authenticated, the devices are transferred from the unapproved state to the approved device list.
    """
    auth_service = securityService.AuthorizationService(db)
    unapproved_operation_service = operationService.UnapprovedOperationService(db)
    session_service = sessionService.SessionService(db)
    auth_service.authenticate_user_card(card_data, "concierge")

    session_service.end_session(session_id)

    operations = unapproved_operation_service.create_operation_from_unappproved(session_id)

    return operations
