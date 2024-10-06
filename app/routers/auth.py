from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from app import database, models, oauth2, schemas
from app.services import securityService, sessionService

router = APIRouter(
    tags=['Authentication']
)

# todo uwierzytelniane zewnetrzne, wysylanie requesta z kartą


@router.post("/login", response_model=schemas.LoginConcierge)
def login(concierge_credentials: OAuth2PasswordRequestForm = Depends(),
          db: Session = Depends(database.get_db)) -> schemas.LoginConcierge:
    """
    Authenticate a concierge using their login credentials (username and password).
    
    This endpoint allows a concierge to log in by providing valid credentials.
    Upon successful authentication, the system generates and returns an access token 
    and a refresh token that can be used for subsequent API requests and token refreshing.

    Args:
        concierge_credentials (OAuth2PasswordRequestForm): The login form containing the username and password.
        db (Session): The active database session.

    Returns:
        LoginConcierge: An object containing both the access token and refresh token.
    
    Raises:
        HTTPException: If authentication fails or if the user does not have the appropriate permissions.
    """
    auth_service = securityService.AuthorizationService(db)
    concierge = auth_service.authenticate_user_login(concierge_credentials.username, concierge_credentials.password, "concierge")

    token_service = securityService.TokenService(db)
    return token_service.generate_tokens(concierge.id, concierge.role.value)


@router.post("/login/card", response_model=schemas.LoginConcierge)
def card_login(card_id: schemas.CardLogin,
               db: Session = Depends(database.get_db)) -> schemas.LoginConcierge:
    """
    Authenticate a concierge using their card ID.

    This endpoint allows a concierge to authenticate by providing their card ID.
    Upon successful authentication, the system generates and returns both an access token 
    and a refresh token for future API requests and token refreshing.

    Args:
        card_id (CardLogin): Object containing the card ID.
        db (Session): The active database session.

    Returns:
        LoginConcierge: An object containing both the access token and refresh token.
    
    Raises:
        HTTPException: If authentication fails or if the user does not have the appropriate permissions.
    """
    auth_service = securityService.AuthorizationService(db)
    concierge = auth_service.authenticate_user_card(card_id, "concierge")

    token_service = securityService.TokenService(db)
    return token_service.generate_tokens(concierge.id, concierge.role.value)


@router.post("/start-session", response_model=schemas.IssueReturnSession)
def start_login_session(user_credentials: OAuth2PasswordRequestForm = Depends(),
                         current_concierge=Depends(oauth2.get_current_concierge),
                         db: Session = Depends(database.get_db)) -> schemas.IssueReturnSession:
    """
    Start an session by authenticating a user with credentials (username and password).

    This endpoint allows a concierge to initiate an session for a user by verifying 
    their login credentials. Once authenticated, the system creates an session for 
    the user and assigns it to the current concierge.

    Args:
        user_credentials (OAuth2PasswordRequestForm): The login credentials (username and password) of the user.
        current_concierge: The currently authenticated concierge (extracted from the OAuth2 token).
        db (Session): The active database session.

    Returns:
        LoginIssueReturnSession: An object containing the ID of the newly created session and the user's details.
    
    Raises:
        HTTPException: If user authentication fails or if the session cannot be created.
    """
    auth_service = securityService.AuthorizationService(db)
    session_service = sessionService.SessionService(db)

    user = auth_service.authenticate_user_login(user_credentials.username, user_credentials.password, "employee")
    session = session_service.create_session(user.id, current_concierge.id)

    return session


@router.post("/start-session/card", response_model=schemas.IssueReturnSession)
def start_card_session(card_id: schemas.CardLogin,
                        current_concierge=Depends(oauth2.get_current_concierge),
                        db: Session = Depends(database.get_db)) -> schemas.IssueReturnSession:
    """
    Start an session by authenticating a user with a card ID.

    This endpoint allows a concierge to initiate an session for a user 
    by verifying their card ID. Once authenticated, the system creates an session 
    for the user and assigns it to the current concierge.
    """
    auth_service = securityService.AuthorizationService(db)
    session_service = sessionService.SessionService(db)
    user = auth_service.authenticate_user_card(card_id, "employee")
    
    session = session_service.create_session(user.id, current_concierge.id)

    return session


@router.post("/refresh", response_model=schemas.Token)
def refresh_token(refresh_token: schemas.RefreshToken, db: Session = Depends(database.get_db)) -> schemas.Token:
    """
    Refresh the access token using a valid refresh token.

    This endpoint allows users to renew their access token by providing 
    a valid refresh token. The system verifies the refresh token and generates a new access token.
    """
    token_service = securityService.TokenService(db)
    token_data = token_service.verify_concierge_token(refresh_token.refresh_token)

    user = db.query(models.User).filter_by(id=token_data.id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    access_token = token_service.create_token(token_data.model_dump(), "access")
    return schemas.Token(access_token=access_token, type="bearer")


@router.post("/logout")
def logout(token: str = Depends(oauth2.get_current_concierge_token),
           db: Session = Depends(database.get_db)) -> JSONResponse:
    """
    Log out the concierge by blacklisting their token.

    This endpoint allows a concierge to log out by adding their access token to a blacklist,
    effectively invalidating it for future requests.
    """
    token_service = securityService.TokenService(db)
    token_data = token_service.verify_concierge_token(token)

    concierge = db.query(models.User).filter_by(id=token_data.id).first()
    if not concierge:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    if token_service.add_token_to_blacklist(token):
        return JSONResponse({"detail": "User logged out successfully"})

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are logged out")
