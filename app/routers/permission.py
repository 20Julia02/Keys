from fastapi import status, HTTPException, Depends, APIRouter
from .. import schema, database, models, utils, oauth2
from sqlalchemy.orm import Session
from typing import List

router = APIRouter(
    prefix="/permissions",
    tags=['Permissions']
)


@router.get("/users/{id}", response_model=List[schema.PermissionOut])
def get_user_permission(id: int,
                        current_user=Depends(oauth2.get_current_user),
                        db: Session = Depends(database.get_db)):
    utils.check_if_admin(current_user)
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User with id: {id} doesn't exist")
    perm = db.query(models.Permission).filter(
        models.Permission.user_id == id).all()
    if not perm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User with id: {id} doesn't have any permission")
    return perm


@router.get("/rooms/{id}", response_model=List[schema.PermissionOut])
def get_key_permission(id: int,
                       current_user=Depends(oauth2.get_current_user),
                       db: Session = Depends(database.get_db)):
    utils.check_if_admin(current_user)
    room = db.query(models.Room).filter(models.Room.id == id).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Room with id: {id} doesn't exist")
    perm = db.query(models.Permission).filter(
        models.Permission.room_id == id).all()
    if not perm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"There is no one with permission to key number {K}")
    return perm
