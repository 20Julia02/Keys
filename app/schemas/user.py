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
