import datetime
from fastapi import Depends, APIRouter, status
from app.schemas import PermissionOut, PermissionCreate
from app import database, oauth2
from sqlalchemy.orm import Session
from typing import Sequence, Optional
import app.models.permission as mpermission
from app.models.user import User
from app.services import securityService
import app.models.user as muser

router = APIRouter(
    prefix="/permissions",
    tags=['Permissions']
)

# todo dane o pozwoleniach brac z systemu pw
# todo sprawdzac date i godzine


@router.get("/", response_model=Sequence[PermissionOut])
def get_permissions(
    user_id: Optional[int] = None,
    room_id: Optional[int] = None,
    date: Optional[datetime.date] = None,
    start_time: Optional[datetime.time] = None,
    current_concierge: User = Depends(oauth2.get_current_concierge),
    db: Session = Depends(database.get_db)
) -> Sequence[PermissionOut]:
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
def create_permission(permission_data: PermissionCreate,
                      db: Session = Depends(database.get_db),
                      current_concierge: User = Depends(oauth2.get_current_concierge)) -> PermissionOut:
    """
    Creates a new permission in the database.
    """
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
def update_permission(permission_id: int,
                      permission_data: PermissionCreate,
                      db: Session = Depends(database.get_db),
                      current_concierge: User = Depends(oauth2.get_current_concierge)) -> PermissionOut:
    """
    Updates an existing permission in the database.
    """
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
def delete_permission(permission_id: int,
                      db: Session = Depends(database.get_db),
                      current_concierge: User = Depends(oauth2.get_current_concierge)):
    """
    Deletes a permission by its ID from the database.
    """
    auth_service = securityService.AuthorizationService(db)
    auth_service.entitled_or_error(muser.UserRole.admin, current_concierge)
    return mpermission.Permission.delete_permission(db, permission_id)
