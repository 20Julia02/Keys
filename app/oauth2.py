from app import database
import app.models.user as muser
from app.services.securityService import AuthorizationService
from fastapi import Depends, Request, HTTPException, status, Response
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.services import securityService
from app.config import logger

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='login')


def get_current_concierge(
    request: Request,
    db: Session = Depends(database.get_db)
) -> muser.User:
    """
    Retrieve the current authenticated concierge based on the access token from cookies.

    Parameters:
    - request (Request): The incoming HTTP request containing the access token in cookies.
    - db (Session): The database session for accessing user services.

    Returns:
    - muser.User: The authenticated concierge object.

    Raises:
    - HTTPException: If the token is missing or invalid.
    """
    logger.info("Attempting to retrieve access token from cookies.")
    
    token = request.cookies.get("access_token")
    if token is None:
        logger.warning("Access token is missing in the request.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.info("Access token found. Verifying and retrieving the current concierge.")
    
    auth_service = AuthorizationService(db)
    concierge = auth_service.get_current_concierge(token)
    
    logger.info(f"Successfully retrieved current concierge: ID {concierge.id}, Role {concierge.role}.")
    return concierge


def get_current_concierge_token(
    request: Request,
    db: Session = Depends(database.get_db)
) -> str:
    """
    Retrieve the current access token for the authenticated concierge from cookies.

    Parameters:
    - request (Request): The incoming HTTP request containing the access token in cookies.
    - db (Session): The database session for accessing token services.

    Returns:
    - str: The access token.

    Raises:
    - HTTPException: If the token is missing or invalid.
    """
    logger.info("Attempting to retrieve access token from cookies.")
    
    token = request.cookies.get("access_token")
    if token is None:
        logger.warning("Access token is missing in the request.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.info("Access token found. Verifying token validity.")
    
    auth_service = AuthorizationService(db)
    valid_token = auth_service.get_current_concierge_token(token)
    
    logger.info("Access token successfully verified and returned.")
    return valid_token

def set_access_token_cookie(response: Response, 
                            user_id: int, 
                            user_role: str, 
                            db: Session) -> str:
    """
    Set an access token as a secure HTTP-only cookie in the response.

    Parameters:
    - response (Response): The HTTP response object to modify.
    - user_id (int): The ID of the user for whom the token is being created.
    - user_role (str): The role of the user for whom the token is being created.
    - db (Session): The database session for accessing token services.

    Returns:
    - str: The created access token.
    """
    logger.info(f"Creating access token for user ID {user_id} with role {user_role}.")
    
    token_service = securityService.TokenService(db)
    access_token = token_service.create_token({"user_id": user_id, "user_role": user_role}, "access")
    
    logger.debug(f"Access token successfully created for user ID {user_id}. Setting token as cookie.")

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # Change to True in production
        max_age=86400,
        samesite="strict"
    )
    
    logger.debug(f"Access token cookie set for user ID {user_id}.")
    return access_token
