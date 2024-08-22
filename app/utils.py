from passlib.context import CryptContext
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from .models import TokenBlacklist

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hashes the given password using the bcrypt algorithm.

    Args:
        password (str): The plain text password to hash.

    Returns:
        str: The hashed password.
    """
    return pwd_context.hash(password)


def verify_hashed(plain_text: str, hashed_text: str) -> bool:
    """
    Verifies that the given plain text password matches the hashed password.

    Args:
        plain_password (str): The plain text password to verify.
        hashed_password (str): The hashed password to compare against.

    Returns:
        bool: True if the passwords match, False otherwise.
    """
    return pwd_context.verify(plain_text, hashed_text)


def check_if_entitled(role: str, current_concierge):
    """
    Checks if the current user has the required role or is an admin.
    Raises an HTTP 403 Forbidden exception if the user is not entitled.

    Args:
        role (str): The required role.
        current_concierge: The current user object, containing the user's role.

    Raises:
        HTTPException: If the user does not have the required role.
    """
    if not (current_concierge.role.value == role or current_concierge.role.value == "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f"You cannot perform this operation without the {role} role")


def is_token_blacklisted(db: Session, token: str) -> bool:
    """
    Checks if a token is in the blacklist.

    Args:
        db (Session): The database session.
        token (str): The token to check.

    Returns:
        bool: True if the token is blacklisted, False otherwise.
    """
    return db.query(TokenBlacklist).filter_by(token=token).first() is not None


def add_token_to_blacklist(db: Session, token: str) -> bool:
    """
    Adds a token to the blacklist in the database.

    Args:
        db (Session): The database session.
        token (str): The token to blacklist.

    Returns:
        bool: True after the token is successfully added to the blacklist.
    """
    if not is_token_blacklisted(db, token):
        db_token = TokenBlacklist(token=token)
        db.add(db_token)
        db.commit()
    return True