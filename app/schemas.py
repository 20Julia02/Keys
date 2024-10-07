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
    email: EmailStr
    password: str
    faculty: Optional[str] = None
    photo_url: Optional[str] = None
    card_code: str


class UserOut(UserBase):
    id: int
    role: str
    faculty: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class DeviceBase(BaseModel):
    code: str
    version: str
    is_taken: bool
    dev_type: str


class DeviceCreate(DeviceBase):
    room_id: int


class RoomOut(BaseModel):
    id: int
    number: str

    model_config = ConfigDict(from_attributes=True)


class DeviceOut(DeviceBase):
    room: RoomOut
    last_taken: Optional[datetime.datetime] = None
    last_returned: Optional[datetime.datetime] = None
    last_owner_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class DeviceUnapproved(BaseModel):
    device_code: str
    is_taken: bool
    last_taken: Optional[datetime.datetime] = None
    last_returned: Optional[datetime.datetime] = None
    last_owner_id: Optional[int] = None
    issue_return_session_id: int

    model_config = ConfigDict(from_attributes=True)


class PermissionCreate(BaseModel):
    user_id: int
    room_id: int
    start_reservation: datetime.datetime
    end_reservation: datetime.datetime


class PermissionOut(BaseModel):
    user: UserOut
    room: RoomOut
    start_reservation: datetime.datetime
    end_reservation: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


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


class UnauthorizedUserCreate(UnauthorizedUserBase):
    addition_time: datetime.datetime


class UnauthorizedUserOut(UnauthorizedUserBase):
    pass

    model_config = ConfigDict(from_attributes=True)


class IssueReturnSession(BaseModel):
    id: int
    user_id: Optional[int] = None
    concierge_id: int
    start_time: datetime.datetime
    status: Optional[str] = "in_progress"

    model_config = ConfigDict(from_attributes=True)


class DeviceOperation(BaseModel):
    device_code: str
    issue_return_session_id: int
    operation_type: str
    entitled: bool


class DeviceNote(BaseModel):
    device_operation: DeviceOperation
    note: str

    model_config = ConfigDict(from_attributes=True)


class DeviceNoteOut(BaseModel):
    device_operation: DeviceOperation
    note: str

    model_config = ConfigDict(from_attributes=True)


class UserNote(BaseModel):
    user: UserOut
    note: str

    model_config = ConfigDict(from_attributes=True)


class ChangeStatus(BaseModel):
    issue_return_session_id: int
    force: Optional[bool] = False


class DetailMessage(BaseModel):
    detail: str


class DeviceOperationOut(BaseModel):
    id: int
    device: DeviceOut
    issue_return_session: IssueReturnSession
    operation_type: str
    entitled: bool

    model_config = ConfigDict(from_attributes=True)


DeviceOperationOrDetailResponse = Union[DeviceOperationOut, DetailMessage]
