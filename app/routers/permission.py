from fastapi import status, Depends, APIRouter, Response, HTTPException

from ..schemas import PermissionOut, PermissionCreate
from .. import database, models, utils, oauth2
from sqlalchemy.orm import Session
from typing import List

router = APIRouter(
    prefix="/permissions",
    tags=['Permissions']
)


router.get("/users/{id}", response_model=List[PermissionOut])
def get_user_permission(id: int,
                        current_user=Depends(oauth2.get_current_user),
                        db: Session = Depends(database.get_db)) -> List[PermissionOut]:
    """
    Retrieves all permissions associated with a specific user.

    Args:
        id (int): The ID of the user.
        current_user: The current user object (used for authorization).
        db (Session): The database session.

    Returns:
        List[PermissionOut]: A list of permissions associated with the user.

    Raises:
        HTTPException: If the user doesn't exist or has no permissions.
    """
    utils.check_if_entitled("concierge", current_user)
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User with id: {id} doesn't exist")
    perm = db.query(models.Permission).filter(
        models.Permission.user_id == id).all()
    if perm is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"There is no one with permission to key number {id}")
    return perm


@router.get("/rooms/{id}", response_model=List[PermissionOut])
def get_key_permission(id: int,
                       current_user=Depends(oauth2.get_current_user),
                       db: Session = Depends(database.get_db)) -> List[PermissionOut]:
    """
    Retrieves all permissions associated with a specific room.

    Args:
        id (int): The ID of the room.
        current_user: The current user object (used for authorization).
        db (Session): The database session.

    Returns:
        List[PermissionOut]: A list of permissions associated with the room.

    Raises:
        HTTPException: If the room doesn't exist or has no permissions.
    """
    utils.check_if_entitled("concierge", current_user)
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
