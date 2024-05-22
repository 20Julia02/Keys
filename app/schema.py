from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class Faculty(BaseModel):
    name: str

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    name: str
    surname: str
    role: str


class UserCreate(UserBase):
    email: EmailStr
    password: str
    faculty_id: int


class UserOut(UserBase):
    id: int
    faculty: Faculty

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: Optional[int] = None
    role: Optional[str] = None


class Room(BaseModel):
    number: int

    class Config:
        from_attributes = True


class KeyBase(BaseModel):
    version: str
    is_taken: bool


class KeyCreate(KeyBase):
    room_id: int

    class Config:
        from_attributes = True


class KeyOut(KeyBase):
    id: int
    room: Room
    last_taken: Optional[datetime]
    last_returned: Optional[datetime]
    # TODO
    # last_owner: Optional[UserOut]

    class Config:
        from_attributes = True


class RoomOut(BaseModel):
    number: int

    class Config:
        from_attributes = True


class PermissionOut(BaseModel):
    user: UserOut
    room: RoomOut
    start_reservation: datetime
    end_reservation: datetime

    class Config:
        from_attributes = True
