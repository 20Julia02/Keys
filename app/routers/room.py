from fastapi import Depends, APIRouter
from typing import List, Optional
from app.schemas import RoomOut
from app import database, oauth2
from sqlalchemy.orm import Session
import app.models.device as mdevice

router = APIRouter(
    prefix="/rooms",
    tags=['Rooms']
)


@router.get("/", response_model=List[RoomOut])
def get_rooms(current_concierge=Depends(oauth2.get_current_concierge),
              number: Optional[str] = None,
              db: Session = Depends(database.get_db)) -> List[RoomOut]:
    """
    Retrieves all rooms from the database that match the specified number.
    """
    return mdevice.Room.get_rooms(db, number)


@router.get("/{room_id}", response_model=RoomOut)
def get_room_id(room_id: int,
                current_concierge=Depends(oauth2.get_current_concierge),
                db: Session = Depends(database.get_db)) -> RoomOut:
    """
    Retrieves a room by its ID from the database.
    """
    return mdevice.Room.get_room_id(db, room_id)
