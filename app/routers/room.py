from fastapi import Depends, APIRouter, status, HTTPException
from typing import List
from ..schemas.room import RoomOut
from .. import database, models, utils, oauth2
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/rooms",
    tags=['Rooms']
)


@router.get("/", response_model=List[RoomOut])
def get_all_users(current_user=Depends(oauth2.get_current_user),
                  db: Session = Depends(database.get_db)):
    utils.check_if_entitled("admin", current_user)
    room = db.query(models.Room).all()
    if room is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="There is no room in database")
    return room


@router.get("/{id}", response_model=RoomOut)
def get_user(id: int,
             current_user=Depends(oauth2.get_current_user),
             db: Session = Depends(database.get_db)):
    utils.check_if_entitled("admin", current_user)
    room = db.query(models.Room).filter(models.Room.id == id).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Room with id: {id} doesn't exist")
    return room
