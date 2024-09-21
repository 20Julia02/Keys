from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from ..schemas import DeviceUnapproved
from .. import database, models, oauth2
from .. import securityService, activityService, deviceService

router = APIRouter(
    prefix="/approve",
    tags=['Approve']
)


@router.get("/unapproved", response_model=DeviceUnapproved)
def get_all_unapproved(current_concierge=Depends(oauth2.get_current_concierge),
                       db: Session = Depends(database.get_db)):
    devs = db.query(models.DevicesUnapproved).all()
    return devs


@router.post("/activity/login")
def approve_activity_login(activity_id: int,
                           db: Session = Depends(database.get_db),
                           concierge_credentials: OAuth2PasswordRequestForm = Depends(),
                           current_concierge=Depends(oauth2.get_current_concierge)) -> JSONResponse:
    """
    Approves operations for a given activity, authenticating using credentials.

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
    activity_service.change_activity_status(activity_id)

    dev_activity = unapproved_dev_service.unapproved_devices_activity(activity_id)
    unapproved_dev_service.transfer_devices(dev_activity)

    return JSONResponse({"detail": "Operations approved and devices updated successfully."})


@router.post("/activity/card")
def approve_activity_card(activity_id: int,
                          concierge_credentials: OAuth2PasswordRequestForm = Depends(),
                          db: Session = Depends(database.get_db),
                          current_concierge=Depends(oauth2.get_current_concierge)) -> JSONResponse:
    """
    Approves operations for a given activity, authenticating using credentials.

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

    activity_service.change_activity_status(activity_id)
    dev_activity = unapproved_dev_service.unapproved_devices_activity(activity_id)
    unapproved_dev_service.transfer_devices(dev_activity)

    return JSONResponse({"detail": "Operations approved and devices updated successfully."})


@router.post("/")
def approve_all_login(concierge_credentials: OAuth2PasswordRequestForm = Depends(),
                      db: Session = Depends(database.get_db),
                      current_concierge=Depends(oauth2.get_current_concierge)) -> JSONResponse:

    auth_service = securityService.AuthorizationService(db)
    unapproved_dev_service = deviceService.UnapprovedDeviceService(db)
    activity_service = activityService.ActivityService(db)

    concierge = auth_service.authenticate_user_login(concierge_credentials.username, concierge_credentials.password)
    auth_service.check_if_entitled("concierge", concierge)

    dev_all = unapproved_dev_service.unapproved_devices_all()

    for dev in dev_all:
        activity_service.change_activity_status(dev.activity_id)
    unapproved_dev_service.transfer_devices(dev_all)

    return JSONResponse({"detail": "All operations approved and devices updated successfully."})
