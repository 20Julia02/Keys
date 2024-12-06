import datetime
from fastapi import Depends, APIRouter, status, Response, Query
from app.schemas import PermissionOut, PermissionCreate
from app import database, oauth2
from sqlalchemy.orm import Session
from typing import Sequence, Optional
import app.models.permission as mpermission
from app.models.user import User
from app.services import securityService
import app.models.user as muser
from app.config import logger

router = APIRouter(
    prefix="/permissions",
    tags=['Permissions']
)


@router.get("/", response_model=Sequence[PermissionOut])
def get_permissions(response: Response,
    user_id: Optional[int] = None,
    room_id: Optional[int] = None,
    date: Optional[datetime.date] = Query(
        None, 
        description="Filter permissions by date. Format: YYYY-MM-DD.", 
        example="2024-12-31"
    ),
    start_time: Optional[datetime.time] = Query(
        None, 
        description="Filter permissions by start time. Format: HH:MM:SS.", 
        example="14:30:00"
    ),
    current_concierge: User = Depends(oauth2.get_current_concierge),
    db: Session = Depends(database.get_db)
) -> Sequence[PermissionOut]:
    """
    Retrieve permissions with optional filtering.

    This endpoint fetches permissions based on provided filters such as user ID, room ID, date, 
    and start time. If no filters are provided, all permissions are returned.

    The operation ensures that the requesting user is authenticated and updates their access token.
    """
    logger.info(
        f"GET request to retrieve permissions by user_id: {user_id}, room_id: {room_id}, date: {date}, start_time: {start_time}")
    oauth2.set_access_token_cookie(response, current_concierge.id, current_concierge.role.value, db)
    return mpermission.Permission.get_permissions(db, user_id, room_id, date, start_time)


@router.post("/",
             response_model=PermissionOut,
             status_code=status.HTTP_201_CREATED,
             responses={
                 201: {
                     "description": "Permission created successfully.",
                     "content": {
                         "application/json": {
                             "example": {
                                 "id": 1,
                                 "user_id": 1,
                                 "room_id": 1,
                                 "date": "2024-11-12",
                                 "start_time": "14:30",
                                 "end_time": "15:30"
                             }
                         }
                     }
                 },
                 400: {
                     "description": "A permission already exists for the specified room and time.",
                     "content": {
                         "application/json": {
                             "example": {
                                 "detail": "A permission already exists for the specified room and time."
                             }
                         }
                     }
                 },
                 500: {
                     "description": "An internal server error occurred.",
                     "content": {
                         "application/json": {
                             "example": {
                                 "detail": "Internal server error"
                             }
                         }
                     }
                 }
             })
def create_permission(response: Response,
                      permission_data: PermissionCreate,
                      db: Session = Depends(database.get_db),
                      current_concierge: User = Depends(oauth2.get_current_concierge)) -> PermissionOut:
    """
    Create a new permission in the database.

    This endpoint allows creating a permission with specific details such as user ID, 
    room ID, date, and time. The requesting user must have the 'admin' role.

    The operation ensures that the requesting user is authenticated and updates their access token.
    """
    logger.info(
        f"POST request to create permission")
    oauth2.set_access_token_cookie(response, current_concierge.id, current_concierge.role.value, db)
    auth_service = securityService.AuthorizationService(db)
    auth_service.entitled_or_error(muser.UserRole.admin, current_concierge)
    return mpermission.Permission.create_permission(db, permission_data)


@router.post("/update/{permission_id}",
             response_model=PermissionOut,
             responses={
                 200: {
                     "description": "Permission updated successfully.",
                     "content": {
                         "application/json": {
                             "example": {
                                 "id": 1,
                                 "user_id": 1,
                                 "room_id": 1,
                                 "date": "2024-11-12",
                                 "start_time": "14:30",
                                 "end_time": "15:30"
                             }
                         }
                     }
                 },
                 400: {
                     "description": "A permission already exists for the specified room and time.",
                     "content": {
                         "application/json": {
                             "example": {
                                 "detail": "A permission already exists for the specified room and time."
                             }
                         }
                     }
                 },
                 404: {
                     "description": "Permission with the specified ID not found.",
                     "content": {
                         "application/json": {
                             "example": {
                                 "detail": "Permission with id: {permission_id} doesn't exist"
                             }
                         }
                     }
                 },
                 500: {
                     "description": "An internal server error occurred.",
                     "content": {
                         "application/json": {
                             "example": {
                                 "detail": "Internal server error"
                             }
                         }
                     }
                 }
             })
def update_permission(response: Response,
                      permission_id: int,
                      permission_data: PermissionCreate,
                      db: Session = Depends(database.get_db),
                      current_concierge: User = Depends(oauth2.get_current_concierge)) -> PermissionOut:
    """
    Update an existing permission in the database.

    This endpoint modifies a permission's details, such as time or room ID, based on the provided
    permission ID. The requesting user must have the 'admin' role.

    The operation ensures that the requesting user is authenticated and updates their access token.
    """
    logger.info(
        f"POST request to update permission with ID {permission_id}")
    oauth2.set_access_token_cookie(response, current_concierge.id, current_concierge.role.value, db)
    auth_service = securityService.AuthorizationService(db)
    auth_service.entitled_or_error(muser.UserRole.admin, current_concierge)
    return mpermission.Permission.update_permission(db, permission_id, permission_data)


@router.delete("/{permission_id}",
               status_code=status.HTTP_204_NO_CONTENT,
               responses={
                   204: {
                       "description": "Permission deleted successfully."
                   },
                   404: {
                       "description": "Permission with the specified ID not found.",
                       "content": {
                           "application/json": {
                               "example": {
                                   "detail": "Permission with id: {permission_id} doesn't exist"
                               }
                           }
                       }
                   },
                   500: {
                       "description": "An internal server error occurred.",
                       "content": {
                           "application/json": {
                               "example": {
                                   "detail": "Internal server error"
                               }
                           }
                       }
                   }
               })
def delete_permission(response: Response,
                      permission_id: int,
                      db: Session = Depends(database.get_db),
                      current_concierge: User = Depends(oauth2.get_current_concierge)):
    """
    Delete a permission from the database by its ID.

    This endpoint removes a permission identified by the given ID. The requesting user must have 
    the 'admin' role. If the ID does not exist, a 404 error is returned.

    The operation ensures that the requesting user is authenticated and updates their access token.
    """
    logger.info(f"DELETE request to delete permission with ID {permission_id}")
    oauth2.set_access_token_cookie(response, current_concierge.id, current_concierge.role.value, db)
    auth_service = securityService.AuthorizationService(db)
    auth_service.entitled_or_error(muser.UserRole.admin, current_concierge)
    return mpermission.Permission.delete_permission(db, permission_id)


@router.get("/active", response_model=Sequence[PermissionOut])
def get_active_permissions(
    response: Response,
    user_id: int,
    date: Optional[datetime.date] = datetime.datetime.now().date(),
    time: Optional[datetime.time] = datetime.datetime.now().time(),
    db: Session = Depends(database.get_db),
    current_concierge: User = Depends(oauth2.get_current_concierge)
) -> Sequence[PermissionOut]:
    """
    Retrieve active permissions for a specific user.

    This endpoint fetches all active permissions for a user at a given date and time. If no 
    date or time is specified, the current date and time are used. Active permissions are 
    those that are valid for the specified time.

    The operation ensures that the requesting user is authenticated and updates their access token.
    """
    logger.info(
        f"GET request to retrieve active permissions for user ID {user_id} at date: {date} and time: {time}")
    oauth2.set_access_token_cookie(response, current_concierge.id, current_concierge.role.value, db)
    return mpermission.Permission.get_active_permissions(db, user_id, date, time)
