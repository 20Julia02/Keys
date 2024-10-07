from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from app.schemas import DeviceUnapproved, CardLogin
from app import database, oauth2
from app.services import securityService, sessionService, deviceService
from typing import List

router = APIRouter(
    tags=['Approve']
)


@router.get("/unapproved/{session_id}",
            response_model=List[DeviceUnapproved],
            responses={
                200: {"description": "List with details of all unapproved devices based on a specific session ID.", },
                401: {"description": "Invalid token or the credentials can not be validated"},
                403: {"description": "You are logged out or you cannot perform the operation with your role"},
                404: {"description": "No unapproved devices found for this session"}
                })
def get_unapproved_device_session(session_id: int,
                                  current_concierge=Depends(oauth2.get_current_concierge),
                                  db: Session = Depends(database.get_db)) -> List[DeviceUnapproved]:
    """
    Retrieve List with details of all unapproved devices based on a specific session ID.

    This endpoint allows the logged-in concierge to access information about a devices
    that were modified during a given session and have not been approved yet.
    """
    unapproved_dev_service = deviceService.UnapprovedDeviceService(db)
    return unapproved_dev_service.get_unapproved_dev_session(session_id)


@router.get("/unapproved", response_model=List[DeviceUnapproved])
def get_all_unapproved(current_concierge=Depends(oauth2.get_current_concierge),
                       db: Session = Depends(database.get_db)) -> List[DeviceUnapproved]:
    """
    Retrieve all unapproved devices stored in the system.

    This endpoint returns a list of all unapproved devices.s
    """
    unapproved_dev_service = deviceService.UnapprovedDeviceService(db)
    return unapproved_dev_service.get_unapproved_dev_all()


@router.post("/approve/login/session/{session_id}")
def approve_session_login(session_id: int,
                          db: Session = Depends(database.get_db),
                          concierge_credentials: OAuth2PasswordRequestForm = Depends(),
                          current_concierge=Depends(oauth2.get_current_concierge)) -> JSONResponse:
    """
    Approve a session and its associated devices using login credentials for authentication.

    This endpoint finalizes an session, allowing a concierge to approve devices
    modified during the session. The concierge must authenticate via login credentials before approval.
    Once approved, the devices are transferred from the unapproved state to the approved device data.
    """
    auth_service = securityService.AuthorizationService(db)
    unapproved_dev_service = deviceService.UnapprovedDeviceService(db)
    session_service = sessionService.SessionService(db)
    auth_service.authenticate_user_login(concierge_credentials.username, concierge_credentials.password, "concierge")
    session_service.end_session(session_id)

    unapproved_dev_service.transfer_devices(session_id)

    return JSONResponse({"detail": "DeviceOperations approved and devices updated successfully."})


@router.post("/approve/card/session/{session_id}")
def approve_session_card(session_id,
                         card_data: CardLogin,
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
    unapproved_dev_service = deviceService.UnapprovedDeviceService(db)
    session_service = sessionService.SessionService(db)
    auth_service.authenticate_user_card(card_data, "concierge")

    session_service.end_session(session_id)

    unapproved_dev_service.transfer_devices(session_id)

    return JSONResponse({"detail": "DeviceOperations approved and devices updated successfully."})


@router.post("/approve/login")
def approve_all_login(concierge_credentials: OAuth2PasswordRequestForm = Depends(),
                      db: Session = Depends(database.get_db),
                      current_concierge=Depends(oauth2.get_current_concierge)) -> JSONResponse:
    """
    Approve all unapproved devices in the system using login credentials for authentication.

    This endpoint allows a concierge to approve all unapproved devices present in the system.
    The concierge must authenticate using login credentials (username and password) to perform this action.
    Once authenticated, all devices are transferred from the unapproved state to the approved device data.
    """
    auth_service = securityService.AuthorizationService(db)
    unapproved_dev_service = deviceService.UnapprovedDeviceService(db)
    session_service = sessionService.SessionService(db)

    auth_service.authenticate_user_login(concierge_credentials.username, concierge_credentials.password, "concierge")

    dev_all = unapproved_dev_service.get_unapproved_dev_all()

    for dev in dev_all:
        session_service.end_session(dev.issue_return_session_id)

    unapproved_dev_service.transfer_devices()

    return JSONResponse({"detail": "All operations approved and devices updated successfully."})

# todo reject
