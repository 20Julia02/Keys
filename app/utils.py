from passlib.context import CryptContext
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from .models import TokenBlacklist

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash(password: str):
    return pwd_context.hash(password)


def verify(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def check_if_entitled(role, current_user):
    if not (current_user.role.value == role or current_user.role.value == "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f"You cannot perform this operation without the {role} role")


def add_token_to_blacklist(db: Session, token: str):
    db_token = TokenBlacklist(token=token)
    db.add(db_token)
    db.commit()


def is_token_blacklisted(db: Session, token: str):
    return db.query(TokenBlacklist).filter_by(token=token).first() is not None
