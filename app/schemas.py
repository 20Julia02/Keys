from datetime import datetime
from typing import Optional, Union
from pydantic import BaseModel, EmailStr, ConfigDict


class CardLogin(BaseModel):
    card_id: str


class UserBase(BaseModel):
    name: str
    surname: str


class UserCreate(UserBase):
    role: str
    email: EmailStr
    password: str
    faculty: Optional[str] = None
    photo_url: Optional[str] = None
    additional_info: Optional[str] = None
    card_code: str


class UserOut(UserBase):
    id: int
    role: str
    faculty: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class NoteCreate(BaseModel):
    additional_info: str


class NoteUserOut(UserBase):
    additional_info: Optional[str] = None


class DeviceBase(BaseModel):
    version: str
    is_taken: bool
    type: str
    code: str


class DeviceCreate(DeviceBase):
    room_id: int

    model_config = ConfigDict(from_attributes=True)


class RoomOut(BaseModel):
    id: int
    number: str

    model_config = ConfigDict(from_attributes=True)


class DeviceOut(DeviceBase):
    id: int
    room: RoomOut
    last_taken: Optional[datetime] = None
    last_returned: Optional[datetime] = None
    last_owner_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class DeviceUnapproved(BaseModel):
    device_id: int
    activity_id: int
    is_taken: bool
    last_taken: Optional[datetime] = None
    last_returned: Optional[datetime] = None
    last_owner_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class DetailMessage(BaseModel):
    detail: str


DeviceOrDetailResponse = Union[DeviceUnapproved, DetailMessage]


class PermissionCreate(BaseModel):
    user_id: int
    room_id: int
    start_reservation: datetime
    end_reservation: datetime


class PermissionOut(BaseModel):
    user: UserOut
    room: RoomOut
    start_reservation: datetime
    end_reservation: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    type: str

    model_config = ConfigDict(from_attributes=True)


class RefreshToken(BaseModel):
    refresh_token: str

    model_config = ConfigDict(from_attributes=True)


class LoginConcierge(Token):
    refresh_token: str


class TokenData(BaseModel):
    id: Optional[int] = None
    role: Optional[str] = None


class TokenDataUser(BaseModel):
    user_id: Optional[int] = None
    activity: Optional[int] = None


class UnauthorizedUserBase(BaseModel):
    name: str
    surname: str


class UnauthorizedUserCreate(UnauthorizedUserBase):
    additional_info: Optional[str] = None
    id_concierge_who_accepted: Optional[int] = None


class UnauthorizedUserOut(UnauthorizedUserBase):
    pass

    model_config = ConfigDict(from_attributes=True)


class Activity(BaseModel):
    id: int
    user_id: Optional[int] = None
    concierge_id: int
    status: str
    start_time: datetime
