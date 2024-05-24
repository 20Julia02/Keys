from pydantic import BaseModel
from datetime import datetime
from . import user, device


class PermissionCreate(BaseModel):
    user_id: int
    room_id: int
    start_reservation: datetime
    end_reservation: datetime


class PermissionOut(BaseModel):
    user: user.UserOut
    room: device.RoomOut
    start_reservation: datetime
    end_reservation: datetime

    class Config:
        from_attributes = True
