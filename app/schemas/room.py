from pydantic import BaseModel


class RoomOut(BaseModel):
    number: int

    class Config:
        from_attributes = True
