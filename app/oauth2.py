from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from .schemas import TokenData
from . import database, models
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .config import settings
from .utils import is_token_blacklisted, check_if_entitled

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='login')

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
REFRESH_TOKEN_EXPIRE_MINUTES = settings.refresh_token_expire_minutes

active_employee = {}

def create_token(data: dict, type: str) -> str:
    """
    Creates a JWT token with the given data and token type (refresh or access).

    Args:
        data (dict): The data to encode in the token.
        type (str): The type of token ('refresh' or 'access').

    Returns:
        str: The encoded JWT token.
    """
    if type == "refresh":
        time_delta = REFRESH_TOKEN_EXPIRE_MINUTES
    elif type == "access":
        time_delta = ACCESS_TOKEN_EXPIRE_MINUTES
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + \
        timedelta(minutes = time_delta)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def verify_token(token: str) -> TokenData:
    """
    Verifies the given JWT token and extracts the token data.

    Args:
        token (str): The JWT token to verify.
        credentials_exception: The exception to raise if the token is invalid.

    Returns:
        TokenData: An object containing the extracted token data (user_id and user_role).

    Raises:
        HTTPException: If the token is invalid or missing required data.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        id = payload.get("user_id")
        role = payload.get("user_role")

        if id is None or role is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                                   detail="Invalid token")
        token_data = TokenData(id=id, role=role)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                                   detail="Invalid token")
    return token_data


def get_current_concierge(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db))->models.User:
    """
    Retrieves the current concierge from the database using the provided JWT token.

    Args:
        token (str): The JWT token.
        db (Session): The database session.

    Returns:
        User: The user object corresponding to the token's concierge ID and role.

    Raises:
        HTTPException: If the token is invalid, blacklisted, or the user is not found.
    """
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                         detail="Could not validate credentials",
                                         headers={"Authenticate": "Bearer"})
    if is_token_blacklisted(db, token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="You are logged out")
        
    token_data = verify_token(token)

    user = db.query(models.User).filter(
        models.User.id == token_data.id,
        models.User.role == token_data.role
    ).first()

    if user is None:
        raise credentials_exception
    return user

def get_current_concierge_token(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db))->str:
    """
    Retrieves the current user's token after validating the user's identity.

    Args:
        token (str): The JWT token.
        db (Session): The database session.

    Returns:
        str: The validated JWT token.
    """
    _ = get_current_concierge(token, db)
    return token
