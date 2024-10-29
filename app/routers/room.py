from fastapi import Depends, APIRouter
from typing import Sequence, Optional
from app.schemas import RoomOut
from app import database, oauth2
from sqlalchemy.orm import Session
import app.models.device as mdevice
from app.models.user import User

router = APIRouter(
    prefix="/rooms",
    tags=['Rooms']
)


@router.get("/", response_model=Sequence[RoomOut])
def get_rooms(current_concierge: User = Depends(oauth2.get_current_concierge),
              number: Optional[str] = None,
              db: Session = Depends(database.get_db)) -> Sequence[RoomOut]:
    """
    Retrieves all rooms from the database that match the specified number.
    """
    return mdevice.Room.get_rooms(db, number)


@router.get("/{room_id}", response_model=RoomOut)
def get_room_id(room_id: int,
                current_concierge: User = Depends(
                    oauth2.get_current_concierge),
                db: Session = Depends(database.get_db)) -> RoomOut:
    """
    Retrieves a room by its ID from the database.
    """
    return mdevice.Room.get_room_id(db, room_id)
