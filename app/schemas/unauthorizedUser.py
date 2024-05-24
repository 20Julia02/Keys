from pydantic import BaseModel


class UnauthorizedUserBase(BaseModel):
    name: str
    surname: str


class UnauthorizedUserCreate(UnauthorizedUserBase):
    additional_info: str


class UnauthorizedUserOut(UnauthorizedUserBase):
    pass

    class Config:
        from_attributes = True
