from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone

from .schemas.token import TokenData
from . import database, models
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .config import settings
from .utils import is_token_blacklisted

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='login/concierge')

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
REFRESH_TOKEN_EXPIRE_MINUTES = settings.refresh_token_expire_minutes


def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + \
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def create_refresh_token(data: dict):
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + \
        timedelta(days=REFRESH_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def verify_token(token: str, credentials_exeption):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        id = payload.get("user_id")
        role = payload.get("user_role")

        if id is None or role is None:
            raise credentials_exeption
        token_data = TokenData(id=id, role=role)
    except JWTError:
        raise credentials_exeption

    return token_data


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exeption = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                         detail="Could not validate credentials",
                                         headers={"Authenticate": "Bearer"})
    if is_token_blacklisted(db, token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="You are logged out")
    tokenOut = verify_token(token, credentials_exeption)

    user = db.query(models.User).filter(models.User.id ==
                                        tokenOut.id, models.User.role == tokenOut.role).first()

    return user


def get_current_user_token(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    _ = get_current_user(token, db)
    return token
