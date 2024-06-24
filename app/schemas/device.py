from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from .room import RoomOut


class DeviceBase(BaseModel):
    version: str
    is_taken: bool
    type: str
    code: str


class DeviceCreate(DeviceBase):
    room_id: int

    class Config:
        from_attributes = True


class DeviceOut(DeviceBase):
    id: int
    room: RoomOut
    last_taken: Optional[datetime]
    last_returned: Optional[datetime]
    # TODO
    # last_owner: Optional[UserOut]

    class Config:
        from_attributes = True
