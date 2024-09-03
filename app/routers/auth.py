from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from ..schemas import RefreshToken, Token, LoginConcierge
from ..schemas import CardLogin
from .. import database, models, utils, oauth2
from .. import securityService

router = APIRouter(
    tags=['Authentication']
)

@router.post("/login", response_model=LoginConcierge)
def login(concierge_credentials: OAuth2PasswordRequestForm = Depends(), 
          db: Session = Depends(database.get_db)) -> LoginConcierge:
    """
    Authenticates a concierge and generates JWT tokens for access and refresh.

    Args:
        concierge_credentials (OAuth2PasswordRequestForm): The concierge credentials (email and password).
        db (Session): The database session.

    Returns:
        LoginConcierge: The access and refresh tokens.

    Raises:
        HTTPException: If the credentials are invalid or the user is not entitled.
    """
    password_service = securityService.PasswordService()
    auth_service = securityService.AuthorizationService(db)

    concierge = db.query(models.User).filter(
        models.User.email == concierge_credentials.username).first()

    if not (concierge and password_service.verify_hashed(concierge_credentials.password,
                                  concierge.password)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Invalid credentials")
    
    
    auth_service.check_if_entitled("concierge", concierge)

    access_token = securityService.TokenService(db).create_token(
        {"user_id": concierge.id, "user_role": concierge.role.value}, "access")
    refresh_token = securityService.TokenService(db).create_token(
        {"user_id": concierge.id, "user_role": concierge.role.value}, "refresh")
    return {"access_token": access_token, "type": "bearer", "refresh_token": refresh_token}


@router.post("/card-login", response_model=LoginConcierge)
def card_login(card_id: CardLogin, 
               db: Session = Depends(database.get_db)) -> LoginConcierge:
    """
    Authenticates a concierge using a card ID and generates JWT tokens for access and refresh.

    Args:
        card_id (CardLogin): The card ID used for login.
        db (Session): The database session.

    Returns:
        LoginConcierge: The access and refresh tokens.

    Raises:
        HTTPException: If the card ID is invalid or the user is not entitled.
    """
    password_service = securityService.PasswordService()
    auth_service = securityService.AuthorizationService(db)

    users = db.query(models.User).filter(
        models.User.card_code.isnot(None)).all()
    if users is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="There is no user in database")
    for user in users:
        if password_service.verify_hashed(card_id.card_id, user.card_code):
            auth_service.check_if_entitled("concierge", user)
            access_token = securityService.TokenService(db).create_token(
                {"user_id": user.id, "user_role": user.role.value}, "access")
            refresh_token = securityService.TokenService(db).create_token(
                {"user_id": user.id, "user_role": user.role.value}, "refresh")
            return {"access_token": access_token, "type": "bearer", "refresh_token": refresh_token}
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Invalid credentials")

@router.post("/start_activity", response_model=Token)
def start_activity(user_credentials: OAuth2PasswordRequestForm = Depends(),
             current_concierge = Depends(oauth2.get_current_concierge),
             db: Session = Depends(database.get_db)) -> Token:
    """
    Validates the provided user credentials, creates new activity and generates JWT tokens for access.

    Args:
        user_credentials (OAuth2PasswordRequestForm): The user credentials (email and password).
        current_concierge: The current user object (used for authorization).
        db (Session): The database session.

    Returns:
        Token: The access token with user ID and activity ID

    Raises:
        HTTPException: If the credentials are invalid.
    """
    password_service = securityService.PasswordService()

    user = db.query(models.User).filter(
        models.User.email == user_credentials.username).first()

    if not (user and password_service.verify_hashed(user_credentials.password,
                                  user.password)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Invalid credentials")
    activity_id = utils.start_activity(db, user.id, current_concierge.id)
    access_token = securityService.TokenService(db).create_token(
        {"user_id": user.id, "activity_id": activity_id}, "access")
    
    return {"access_token": access_token, "type": "bearer"}

#TODO
#no nwm czy to tak może być
@router.post("/refresh", response_model=Token)
def refresh_token(refresh_token: RefreshToken, 
                  db: Session = Depends(database.get_db)) -> Token:
    """
    Generates a new access token using the provided refresh token.

    Args:
        refresh_token (str): The refresh token.
        db (Session): The database session.

    Returns:
        Token: The new access token.

    Raises:
        HTTPException: If the refresh token is invalid
    """

    token_data = securityService.TokenService(db).verify_concierge_token(refresh_token.refresh_token)

    user = db.query(models.User).filter(models.User.id == token_data.id).first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    access_token = securityService.TokenService(db).create_token(token_data.model_dump(), "access")
    return {"access_token": access_token, "type": "bearer"}


@router.post("/logout")
def logout(token: str = Depends(oauth2.get_current_concierge_token), 
           db: Session = Depends(database.get_db)) -> JSONResponse:
    """
    Logs out the current concierge by blacklisting their token.

    Args:
        token (str): The JWT token to blacklist.
        db (Session): The database session.

    Returns:
        JSONResponse: A response indicating the logout status.

    Raises:
        HTTPException: If the token is invalid or the concierge is already logged out.
    """
    token_data = securityService.TokenService(db).verify_concierge_token(token)
    concierge = db.query(models.User).filter(models.User.id == token_data.id).first()
    
    if not concierge:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    

    token_service = securityService.TokenService(db)
    if token_service.add_token_to_blacklist(token):
        return JSONResponse({'result': True})
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                        detail="You are logged out")

# @router.post("/approve")
# def approve_uperations(
#     id: int,
#     db: Session = Depends(database.get_db),
#     current_concierge: int = Depends(oauth2.get_current_concierge))