import datetime
from typing import Optional, Union
from pydantic import BaseModel, EmailStr, ConfigDict

# todo uporządkować to


class CardLogin(BaseModel):
    card_id: str


class UserBase(BaseModel):
    name: str
    surname: str


class UserCreate(UserBase):
    role: str
    email: str
    password: str
    faculty: Optional[str] = None
    photo_url: Optional[str] = None
    card_code: str


class UserOut(UserBase):
    id: int
    role: str
    faculty: Optional[str]


class DeviceBase(BaseModel):
    code: str
    dev_version: str
    dev_type: str


class DeviceCreate(DeviceBase):
    room_id: int


class RoomOut(BaseModel):
    id: int
    number: str

    model_config = ConfigDict(from_attributes=True)


class DeviceOutNote(BaseModel):
    id: int
    dev_type: str
    dev_version: str
    room_number: str
    is_taken: bool
    has_note: bool


class DeviceOut(BaseModel):
    id: int
    code: str
    dev_type: str
    dev_version: str
    room: RoomOut

    model_config = ConfigDict(from_attributes=True)


class UserDeviceOut(BaseModel):
    id: int
    dev_type: str
    dev_version: str
    room_number: str
    is_taken: bool
    taken_at: datetime.datetime


class PermissionCreate(BaseModel):
    user_id: int
    room_id: int
    start_reservation: datetime.datetime
    end_reservation: datetime.datetime


class PermissionOut(BaseModel):
    room: RoomOut
    user: UserOut
    start_reservation: datetime.datetime
    end_reservation: datetime.datetime


class Token(BaseModel):
    access_token: str
    token_type: str

    model_config = ConfigDict(from_attributes=True)


class RefreshToken(BaseModel):
    refresh_token: str

    model_config = ConfigDict(from_attributes=True)


class LoginConcierge(Token):
    refresh_token: str


class TokenData(BaseModel):
    id: Optional[int] = None
    role: Optional[str] = None


class UnauthorizedUserBase(BaseModel):
    name: str
    surname: str
    email: str


class UnauthorizedUser(UnauthorizedUserBase):
    addition_time: datetime.datetime


class IssueReturnSession(BaseModel):
    id: int
    user_id: Optional[int] = None
    concierge_id: int
    start_time: datetime.datetime
    status: Optional[str] = "in_progress"

    model_config = ConfigDict(from_attributes=True)


class DeviceOperation(BaseModel):
    device_id: int
    session_id: int
    operation_type: str
    entitled: bool


class DeviceNote(BaseModel):
    device_id: int
    note: str

    model_config = ConfigDict(from_attributes=True)


class DeviceNoteOut(BaseModel):
    device: DeviceOut
    note: str

    model_config = ConfigDict(from_attributes=True)


class UserNote(BaseModel):
    user: UserOut
    note: str

    model_config = ConfigDict(from_attributes=True)


class UserNoteCreate(BaseModel):
    user_id: int
    note: str

    model_config = ConfigDict(from_attributes=True)


class ChangeStatus(BaseModel):
    device_id: int
    session_id: int
    force: Optional[bool] = False


class DetailMessage(BaseModel):
    detail: str


class DeviceOperationOut(BaseModel):
    id: int
    device: DeviceOut
    session: IssueReturnSession
    operation_type: str
    entitled: bool
    timestamp: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


DeviceOperationOrDetailResponse = Union[DeviceOperationOut, DetailMessage]
