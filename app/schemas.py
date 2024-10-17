import datetime
from typing import Optional, Union
from pydantic import BaseModel, ConfigDict, Field

# todo uporządkować to


class CardId(BaseModel):
    card_id: str


class RefreshToken(BaseModel):
    refresh_token: str

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str


class TokenData(BaseModel):
    id: Optional[int] = None
    role: Optional[str] = None


class UserCreate(BaseModel):
    name: str
    surname: str
    role: str
    email: str
    password: str
    card_code: str
    faculty: Optional[str] = None
    photo_url: Optional[str] = None


class UserOut(BaseModel):
    id: int
    name: str
    surname: str
    role: str
    faculty: Optional[str]
    photo_url: Optional[str] = None
    

class UnauthorizedUser(BaseModel):
    name: str
    surname: str
    email: str
    addition_time: Optional[datetime.datetime] = None


class RoomOut(BaseModel):
    id: int
    number: str

    model_config = ConfigDict(from_attributes=True)


class DeviceCreate(BaseModel):
    code: str
    dev_version: str
    dev_type: str
    room_id: int


class DeviceOut(BaseModel):
    id: int
    code: str
    dev_type: str
    dev_version: str
    room: RoomOut

    model_config = ConfigDict(from_attributes=True)


class DeviceOutWithNote(BaseModel):
    id: int
    dev_type: str
    dev_version: str
    room_number: str
    is_taken: bool
    has_note: bool


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
    id: int
    device: DeviceOut
    note: str

    model_config = ConfigDict(from_attributes=True)


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


class IssueReturnSession(BaseModel):
    id: int
    user_id: Optional[int] = None
    concierge_id: int
    start_time: datetime.datetime
    status: Optional[str] = "in_progress"

    model_config = ConfigDict(from_attributes=True)


class UserNote(BaseModel):
    id: int
    user: UserOut
    note: str

    model_config = ConfigDict(from_attributes=True)


class UserNoteCreate(BaseModel):
    user_id: int
    note: str

    model_config = ConfigDict(from_attributes=True)

class NoteUpdate(BaseModel):
    note: Optional[str]

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
