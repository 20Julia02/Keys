from typing import Optional
from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    type: str

    class Config:
        from_attributes = True


class RefreshToken(Token):
    refresh_token: str


class TokenData(BaseModel):
    id: Optional[int] = None
    role: Optional[str] = None
