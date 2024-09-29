from fastapi import status, Depends, APIRouter, HTTPException

from app.schemas import PermissionOut, PermissionCreate
from app import database, models, oauth2
from app.services import securityService
from sqlalchemy.orm import Session
from typing import List

router = APIRouter(
    prefix="/permissions",
    tags=['Permissions']
)
#todo
#dane o pozwoleniach brac z systemu pw

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
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User with id: {id} doesn't exist")

    perm = db.query(models.Permission).filter(
        models.Permission.user_id == id).all()
    if not perm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"There is no one with id {id} who has permission")
    return perm


@router.get("/rooms/{id}", response_model=List[PermissionOut])
def get_key_permission(id: int,
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
    room = db.query(models.Room).filter(models.Room.id == id).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Room with id: {id} doesn't exist")
    perm = db.query(models.Permission).filter(
        models.Permission.room_id == id).all()
    if perm is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"There is no one with permission to key number {id}")
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
    new_permission = models.Permission(**permission.model_dump())
    db.add(new_permission)
    db.commit()
    db.refresh(new_permission)
    return new_permission
