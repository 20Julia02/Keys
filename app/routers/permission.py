from fastapi import status, Depends, APIRouter, HTTPException

from app.schemas import PermissionOut, PermissionCreate
from app import database, oauth2
from app.services import securityService, permissionService
from sqlalchemy.orm import Session
from typing import List

router = APIRouter(
    prefix="/permissions",
    tags=['Permissions']
)

# todo dane o pozwoleniach brac z systemu pw
# todo sprawdzac date i godzine
@router.get("/}", response_model=List[PermissionOut])
def get_all_permissions(current_concierge=Depends(oauth2.get_current_concierge),
                        db: Session = Depends(database.get_db)) -> List[PermissionOut]:
    permission_service = permissionService.PermissionService(db)
    perm = permission_service.get_all_permissions()
    return perm

@router.get("/users/{id}", response_model=List[PermissionOut])
def get_user_permission(id: int,
                        current_concierge=Depends(oauth2.get_current_concierge),
                        db: Session = Depends(database.get_db)) -> List[PermissionOut]:
    """
    Retrieves all permissions associated with a specific user.

    Args:
        id (int): The ID of the user.
        current_concierge: The current user object (used for authorization).
        db (Session): The database session.

    Returns:
        List[PermissionOut]: A list of permissions associated with the user.

    Raises:
        HTTPException: If the user doesn't exist or has no permissions.
    """
    permission_service = permissionService.PermissionService(db)
    perm = permission_service.get_user_permission(id)
    return perm


@router.get("/rooms/{id}", response_model=List[PermissionOut])
def get_room_permission(id: int,
                        current_concierge=Depends(oauth2.get_current_concierge),
                        db: Session = Depends(database.get_db)) -> List[PermissionOut]:
    """
    Retrieves all permissions associated with a specific room.

    Args:
        id (int): The ID of the room.
        current_concierge: The current user object (used for authorization).
        db (Session): The database session.

    Returns:
        List[PermissionOut]: A list of permissions associated with the room.

    Raises:
        HTTPException: If the room doesn't exist or has no permissions.
    """
    permission_service = permissionService.PermissionService(db)
    perm = permission_service.get_room_permission(id)

    return perm


@router.post("/", response_model=PermissionOut)
def create_permission(permission: PermissionCreate,
                      current_concierge=Depends(oauth2.get_current_concierge),
                      db: Session = Depends(database.get_db)):
    """
    Creates a new permission entry in the database.

    Args:
        permission: The permission data to be created.
        current_concierge: The currently authenticated user.
        db: Database session.

    Returns:
        The newly created permission record.

    Raises:
        HTTPException: If the user is not entitled.
    """

    auth_service = securityService.AuthorizationService(db)
    auth_service.check_if_entitled("admin", current_concierge)
    permission_service = permissionService.PermissionService(db)
    new_permission = permission_service.create_permission(permission)
    return new_permission
