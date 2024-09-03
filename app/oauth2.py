from . import database, models
from .securityService import AuthorizationService
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='login')

def get_current_concierge(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(database.get_db)
) -> models.User:
    """
    Retrieves the currently authenticated concierge based on the provided token.

    This function uses the `AuthorizationService` to decode the token and retrieve
    the current concierge (user) from the database.

    Args:
        token (str): The authentication token provided by the client.
        db (Session): The database session used to interact with the database.

    Returns:
        models.User: The user object representing the current concierge.

    Raises:
        HTTPException: If the token is invalid or the concierge is not found.
    """
    auth_service = AuthorizationService(db)
    return auth_service.get_current_concierge(token)

def get_current_concierge_token(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(database.get_db)
) -> str:
    """
    Retrieves the token associated with the currently authenticated concierge.

    This function uses the `AuthorizationService` to validate and return the token 
    associated with the current concierge.

    Args:
        token (str): The authentication token provided by the client.
        db (Session): The database session used to interact with the database.

    Returns:
        str: The validated token of the current concierge.

    Raises:
        HTTPException: If the token is invalid.
    """
    auth_service = AuthorizationService(db)
    return auth_service.get_current_concierge_token(token)
