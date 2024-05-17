from pydantic import BaseModel, EmailStr


class Faculty(BaseModel):
    name: str

    class Config:
        orm_mode = True


class Position(BaseModel):
    name: str

    class Config:
        orm_mode = True


class UserCreate(BaseModel):
    name: str
    surname: str
    faculty_id: int
    position_id: int
    isGuest: bool
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    surname: str
    faculty: Faculty
    position: Position
    isGuest: bool

    class Config:
        from_attributes = True
