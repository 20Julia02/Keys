from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from app import models, schemas


class RoomService:
    def __init__(self, db: Session):
        self.db = db

    def get_rooms(self, room_number: Optional[str] = None) -> List[schemas.RoomOut]:
        query = self.db.query(models.Room)
        if room_number:
            query = query.filter(models.Room.number == room_number)
        rooms = query.all()
        if rooms is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="There is no room in database")
        return rooms

    def get_room_id(self, room_id: int) -> schemas.RoomOut:
        room = self.db.query(models.Room).filter(models.Room.id == room_id).first()
        if not room:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Room with id: {room_id} doesn't exist")
        return room
