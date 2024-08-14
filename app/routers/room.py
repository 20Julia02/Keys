from fastapi import Depends, APIRouter, status, HTTPException
from typing import List
from ..schemas import RoomOut
from .. import database, models, utils, oauth2
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/rooms",
    tags=['Rooms']
)


@router.get("/", response_model=List[RoomOut])
def get_all_rooms(current_user=Depends(oauth2.get_current_user),
                  number: str = "",
                  db: Session = Depends(database.get_db)) -> List[RoomOut]:
    """
    Retrieves all rooms from the database that match the specified number.

    Args:
        current_user: The current user object (used for authorization).
        number (str): The room number to filter by.
        db (Session): The database session.

    Returns:
        List[RoomOut]: A list of rooms that match the specified number.

    Raises:
        HTTPException: If no rooms are found in the database.
    """
    utils.check_if_entitled("admin", current_user)
    room = db.query(models.Room).filter(models.Room.number == number).all()
    if room is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="There is no room in database")
    return room



@router.get("/{id}", response_model=RoomOut)
def get_room(id: int,
             current_user=Depends(oauth2.get_current_user),
             db: Session = Depends(database.get_db)) -> RoomOut:
    """
    Retrieves a room by its ID from the database.

    Args:
        id (int): The ID of the room.
        current_user: The current user object (used for authorization).
        db (Session): The database session.

    Returns:
        RoomOut: The room with the specified ID.

    Raises:
        HTTPException: If the room with the specified ID doesn't exist.
    """
    utils.check_if_entitled("admin", current_user)
    room = db.query(models.Room).filter(models.Room.id == id).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Room with id: {id} doesn't exist")
    return room
