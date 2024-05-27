from fastapi import status, Depends, APIRouter, Response, HTTPException

from ..schemas.permission import PermissionOut, PermissionCreate
from .. import database, models, utils, oauth2
from sqlalchemy.orm import Session
from typing import List

router = APIRouter(
    prefix="/permissions",
    tags=['Permissions']
)


@router.get("/users/{id}", response_model=List[PermissionOut])
def get_user_permission(id: int,
                        current_user=Depends(oauth2.get_current_user),
                        db: Session = Depends(database.get_db)):
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
                       db: Session = Depends(database.get_db)):
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


@router.post("/", status_code=status.HTTP_201_CREATED,
             response_model=PermissionOut)
def add_permission(
    permission: PermissionCreate,
    db: Session = Depends(database.get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    utils.check_if_entitled("admin", current_user)
    new_perm = models.Permission(**permission.model_dump())
    db.add(new_perm)
    db.commit()
    db.refresh(new_perm)
    return new_perm


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_permission(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    utils.check_if_entitled("admin", current_user)
    perm = db.query(models.Permission).filter(models.Permission.id == id)
    if perm is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"There's no permission with the id {id}")
    perm.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
