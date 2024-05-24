from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class Room(BaseModel):
    number: int

    class Config:
        from_attributes = True


class RoomOut(BaseModel):
    number: int

    class Config:
        from_attributes = True


class DeviceBase(BaseModel):
    version: str
    is_taken: bool


class DeviceCreate(DeviceBase):
    room_id: int

    class Config:
        from_attributes = True


class DeviceOut(DeviceBase):
    id: int
    room: Room
    last_taken: Optional[datetime]
    last_returned: Optional[datetime]
    # TODO
    # last_owner: Optional[UserOut]

    class Config:
        from_attributes = True
