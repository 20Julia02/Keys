from pydantic import BaseModel, EmailStr


class CardLogin(BaseModel):
    card_id: str


class UserBase(BaseModel):
    name: str
    surname: str
    role: str


class UserCreate(UserBase):
    email: EmailStr
    password: str
    faculty: str
    card_code: str


class UserOut(UserBase):
    id: int
    faculty: str

    class Config:
        from_attributes = True
