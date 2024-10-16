from fastapi import Depends, APIRouter
from typing import List, Optional
from app.schemas import RoomOut
from app import database, oauth2
from app.services import roomService
from sqlalchemy.orm import Session

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
    room_service = roomService.RoomService(db)
    return room_service.get_rooms(number)


@router.get("/{room_id}", response_model=RoomOut)
def get_room_id(room_id: int,
                current_concierge=Depends(oauth2.get_current_concierge),
                db: Session = Depends(database.get_db)) -> RoomOut:
    """
    Retrieves a room by its ID from the database.
    """
    room_service = roomService.RoomService(db)
    return room_service.get_room_id(room_id)
