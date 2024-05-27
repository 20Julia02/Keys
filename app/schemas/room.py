from pydantic import BaseModel


class RoomOut(BaseModel):
    id: int
    number: str

    class Config:
        from_attributes = True
