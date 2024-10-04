from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from app.schemas import DeviceUnapproved, CardLogin
from app import database, oauth2
from app.services import securityService, activityService, deviceService
from typing import List

router = APIRouter(
    prefix="/approve",
    tags=['Approve']
)


@router.get("/unapproved/{activity_id}", response_model=DeviceUnapproved)
def get_unapproved_activity_id(activity_id,
                               current_concierge=Depends(oauth2.get_current_concierge),
                               db: Session = Depends(database.get_db)) -> DeviceUnapproved:
    """
    Returns unapproved device based on the activity id.

    Args:
        activity_id (int): The activity's ID.
        current_concierge: Currently logged-in user (concierge).
        db (Session): Database session.

    Returns:
        DeviceUnapproved: object of unapproved divice created during the activity with given ID
    """
    unapproved_dev_service = deviceService.UnapprovedDeviceService(db)
    return unapproved_dev_service.get_unapproved_dev_activity(activity_id)


@router.get("/unapproved", response_model=List[DeviceUnapproved])
def get_all_unapproved(current_concierge=Depends(oauth2.get_current_concierge),
                       db: Session = Depends(database.get_db)) -> List[DeviceUnapproved]:
    """
    Returns all unapproved devices form database

    Args:
        current_concierge: Currently logged-in user (concierge).
        db (Session): Database session.

    Returns:
        List[DeviceUnapproved]: List of unapproved devices
    """
    unapproved_dev_service = deviceService.UnapprovedDeviceService(db)
    return unapproved_dev_service.get_unapproved_dev_all()


@router.post("/activity/login/{activity_id}")
def approve_activity_login(activity_id: int,
                           db: Session = Depends(database.get_db),
                           concierge_credentials: OAuth2PasswordRequestForm = Depends(),
                           current_concierge=Depends(oauth2.get_current_concierge)) -> JSONResponse:
    """
    Approves operations for a given activity, authenticating concierge using credentials.

    Args:
        activity_id (int): The activity's ID.
        db (Session): Database session.
        concierge_credentials (OAuth2PasswordRequestForm): Form with login credentials.
        current_concierge: Currently logged-in user (concierge).

    Returns:
        JSONResponse: Object indicating the result of the approval operation.
    """
    auth_service = securityService.AuthorizationService(db)
    unapproved_dev_service = deviceService.UnapprovedDeviceService(db)
    activity_service = activityService.ActivityService(db)

    concierge = auth_service.authenticate_user_login(concierge_credentials.username, concierge_credentials.password)
    auth_service.check_if_entitled("concierge", concierge)
    activity_service.end_activity(activity_id)

    dev_activity = unapproved_dev_service.get_unapproved_dev_activity(activity_id)
    unapproved_dev_service.transfer_devices(dev_activity)

    return JSONResponse({"detail": "Operations approved and devices updated successfully."})


@router.post("/activity/card/{activity_id}")
def approve_activity_card(activity_id: int,
                          card_data: CardLogin,
                          db: Session = Depends(database.get_db),
                          current_concierge=Depends(oauth2.get_current_concierge)
                          ) -> JSONResponse:
    """
    Approves operations for a given activity, authenticating using credentials.
    It changes activity status to completed and transfers data from UnapprovedDevices to Devices.

    Args:
        activity_id (int): The activity's ID.
        db (Session): Database session.
        concierge_credentials (OAuth2PasswordRequestForm): Form with login credentials.
        current_concierge: Currently logged-in user (concierge).

    Returns:
        JSONResponse: Object indicating the result of the approval operation.
    """
    auth_service = securityService.AuthorizationService(db)
    unapproved_dev_service = deviceService.UnapprovedDeviceService(db)
    activity_service = activityService.ActivityService(db)
    concierge = auth_service.authenticate_user_card(card_data)

    auth_service.check_if_entitled("concierge", concierge)
    activity_service.end_activity(activity_id)
    dev_activity = unapproved_dev_service.get_unapproved_dev_activity(activity_id)

    unapproved_dev_service.transfer_devices(dev_activity)
    return JSONResponse({"detail": "Operations approved and devices updated successfully."})


@router.post("/")
def approve_all_login(concierge_credentials: OAuth2PasswordRequestForm = Depends(),
                      db: Session = Depends(database.get_db),
                      current_concierge=Depends(oauth2.get_current_concierge)) -> JSONResponse:
    """
    Approves all unapproved devices in database and changes the data in the Devices table
     according to the given data of unapproved devices

    Args:
        concierge_credentials (OAuth2PasswordRequestForm): Form with login credentials.
        current_concierge: Currently logged-in user (concierge).
        db (Session): Database session.

    Returns:
        JSONResponse: information that all operations approved and devices updated successfully.
    """

    auth_service = securityService.AuthorizationService(db)
    unapproved_dev_service = deviceService.UnapprovedDeviceService(db)
    activity_service = activityService.ActivityService(db)

    concierge = auth_service.authenticate_user_login(concierge_credentials.username, concierge_credentials.password)
    auth_service.check_if_entitled("concierge", concierge)

    dev_all = unapproved_dev_service.get_unapproved_dev_all()

    for dev in dev_all:
        activity_service.end_activity(dev.activity_id)
    unapproved_dev_service.transfer_devices(dev_all)

    return JSONResponse({"detail": "All operations approved and devices updated successfully."})
