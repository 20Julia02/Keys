from passlib.context import CryptContext
from fastapi import HTTPException, status

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash(password: str):
    return pwd_context.hash(password)


def verify(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def check_if_entitled(role, current_user):
    if not (current_user.role.value == role or current_user.role.value == "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f"You cannot perform this operation without the {role} role")


def is_not_found(item, message: str):
    if (not item) or (item is None):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=message)
