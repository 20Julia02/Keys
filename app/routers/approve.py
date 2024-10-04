from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from app.schemas import DeviceUnapproved, CardLogin
from app import database, oauth2
from app.services import securityService, activityService, deviceService
from typing import List

router = APIRouter(
    tags=['Approve']
)


@router.get("/unapproved/{activity_id}", response_model= List[DeviceUnapproved])
def get_unapproved_activity_id(activity_id,
                               current_concierge=Depends(oauth2.get_current_concierge),
                               db: Session = Depends(database.get_db)) ->  List[DeviceUnapproved]:
    """
    Retrieve List with details of all unapproved devices based on a specific activity ID.
    
    This endpoint allows the logged-in concierge to access information about a devices
    that were modified during a given activity and have not been approved yet. 
    
    Args:
        activity_id (int): The unique identifier of the activity associated with the device.
        current_concierge: The currently authenticated concierge (extracted from the OAuth2 token).
        db (Session): The active database session.

    Returns:
        List[DeviceUnapproved]: A list of objects containing the details of the unapproved device 
        related to the specified activity.
    
    Raises:
        HTTPException: If no unapproved device is found for the given activity ID.
    """
    unapproved_dev_service = deviceService.UnapprovedDeviceService(db)
    return unapproved_dev_service.get_unapproved_dev_activity(activity_id)


@router.get("/unapproved", response_model=List[DeviceUnapproved])
def get_all_unapproved(current_concierge=Depends(oauth2.get_current_concierge),
                       db: Session = Depends(database.get_db)) -> List[DeviceUnapproved]:
    """
    Retrieve all unapproved devices stored in the system.
    
    This endpoint returns a list of all unapproved devices.
    
    Args:
        current_concierge: The currently authenticated concierge (extracted from the OAuth2 token).
        db (Session): The active database session.

    Returns:
        List[DeviceUnapproved]:  A list of objects containing the details of all unapproved devices.
    
    Raises:
        HTTPException: If no unapproved devices are found in the database.
    """
    unapproved_dev_service = deviceService.UnapprovedDeviceService(db)
    return unapproved_dev_service.get_unapproved_dev_all()


@router.post("/approve/login/activity/{activity_id}")
def approve_activity_login(activity_id: int,
                           db: Session = Depends(database.get_db),
                           concierge_credentials: OAuth2PasswordRequestForm = Depends(),
                           current_concierge=Depends(oauth2.get_current_concierge)) -> JSONResponse:
    """
    Approve an activity and its associated devices using login credentials for authentication.
    
    This endpoint finalizes an activity, allowing a concierge to approve devices 
    modified during the activity. The concierge must authenticate via login credentials before approval.
    Once approved, the devices are transferred from the unapproved state to the approved device data.
    
    Args:
        activity_id (int): The unique identifier of the activity being approved.
        db (Session): The active database session.
        concierge_credentials (OAuth2PasswordRequestForm): The login credentials (username and password).
        current_concierge: The currently authenticated concierge (extracted from the OAuth2 token).

    Returns:
        JSONResponse: A success message indicating the operation was completed and devices were approved.
    
    Raises:
        HTTPException: If authentication fails or if there are issues with approving the activity or devices.
    """
    auth_service = securityService.AuthorizationService(db)
    unapproved_dev_service = deviceService.UnapprovedDeviceService(db)
    activity_service = activityService.ActivityService(db)

    concierge = auth_service.authenticate_user_login(concierge_credentials.username, concierge_credentials.password, "concierge")
    activity_service.end_activity(activity_id)

    dev_activity = unapproved_dev_service.get_unapproved_dev_activity(activity_id)
    unapproved_dev_service.transfer_devices(dev_activity)

    return JSONResponse({"detail": "Operations approved and devices updated successfully."})


@router.post("/approve/card/activity/{activity_id}")
def approve_activity_card(activity_id: int,
                          card_data: CardLogin,
                          db: Session = Depends(database.get_db),
                          current_concierge=Depends(oauth2.get_current_concierge)
                          ) -> JSONResponse:
    """
    Approve an activity and its associated devices using card credentials for authentication.
    
    This endpoint finalizes an activity, allowing a concierge to approve devices 
    used during the activity. The concierge must authenticate using card-based credentials (an ID card).
    Once authenticated, the devices are transferred from the unapproved state to the approved device list.
    
    Args:
        activity_id (int): The unique identifier of the activity being approved.
        card_data (CardLogin): The card code used for authentication.
        db (Session): The active database session.
        current_concierge: The currently authenticated concierge (extracted from the OAuth2 token).

    Returns:
        JSONResponse: A success message indicating the operation was completed and devices were approved.
    
    Raises:
        HTTPException: If card-based authentication fails or if there are issues with approving the activity or devices.
    """
    auth_service = securityService.AuthorizationService(db)
    unapproved_dev_service = deviceService.UnapprovedDeviceService(db)
    activity_service = activityService.ActivityService(db)
    auth_service.authenticate_user_card(card_data, "concierge")

    activity_service.end_activity(activity_id)
    dev_activity = unapproved_dev_service.get_unapproved_dev_activity(activity_id)

    unapproved_dev_service.transfer_devices(dev_activity)
    return JSONResponse({"detail": "Operations approved and devices updated successfully."})


@router.post("/approve/login")
def approve_all_login(concierge_credentials: OAuth2PasswordRequestForm = Depends(),
                      db: Session = Depends(database.get_db),
                      current_concierge=Depends(oauth2.get_current_concierge)) -> JSONResponse:
    """
    Approve all unapproved devices in the system using login credentials for authentication.
    
    This endpoint allows a concierge to approve all unapproved devices present in the system.
    The concierge must authenticate using login credentials (username and password) to perform this action.
    Once authenticated, all devices are transferred from the unapproved state to the approved device data.
    
    Args:
        concierge_credentials (OAuth2PasswordRequestForm): The login credentials (username and password).
        db (Session): The active database session.
        current_concierge: The currently authenticated concierge (extracted from the OAuth2 token).

    Returns:
        JSONResponse: A success message indicating that all unapproved devices were successfully approved.
    
    Raises:
        HTTPException: If authentication fails or if there are issues with approving the devices.
    """

    auth_service = securityService.AuthorizationService(db)
    unapproved_dev_service = deviceService.UnapprovedDeviceService(db)
    activity_service = activityService.ActivityService(db)

    concierge = auth_service.authenticate_user_login(concierge_credentials.username, concierge_credentials.password, "concierge")

    dev_all = unapproved_dev_service.get_unapproved_dev_all()

    for dev in dev_all:
        activity_service.end_activity(dev.activity_id)
    unapproved_dev_service.transfer_devices(dev_all)

    return JSONResponse({"detail": "All operations approved and devices updated successfully."})
