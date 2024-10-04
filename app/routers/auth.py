from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from app.schemas import RefreshToken, Token, LoginConcierge, CardLogin, LoginActivity
from app import database, models, oauth2
from app.services import securityService, activityService

router = APIRouter(
    tags=['Authentication']
)

# todo uwierzytelniane zewnetrzne, wysylanie requesta z kartą


@router.post("/login", response_model=LoginConcierge)
def login(concierge_credentials: OAuth2PasswordRequestForm = Depends(),
          db: Session = Depends(database.get_db)) -> LoginConcierge:
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
    concierge = auth_service.authenticate_user_login(concierge_credentials.username, concierge_credentials.password)
    auth_service.check_if_entitled("concierge", concierge)

    token_service = securityService.TokenService(db)
    return token_service.generate_tokens(concierge.id, concierge.role.value)


@router.post("/card-login", response_model=LoginConcierge)
def card_login(card_id: CardLogin,
               db: Session = Depends(database.get_db)) -> LoginConcierge:
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
    concierge = auth_service.authenticate_user_card(card_id)
    auth_service.check_if_entitled("concierge", concierge)

    token_service = securityService.TokenService(db)
    return token_service.generate_tokens(concierge.id, concierge.role.value)


@router.post("/start-activity", response_model=LoginActivity)
def start_login_activity(user_credentials: OAuth2PasswordRequestForm = Depends(),
                         current_concierge=Depends(oauth2.get_current_concierge),
                         db: Session = Depends(database.get_db)) -> LoginActivity:
    """
    Start an activity by authenticating a user with credentials (username and password).

    This endpoint allows a concierge to initiate an activity for a user by verifying 
    their login credentials. Once authenticated, the system creates an activity for 
    the user and assigns it to the current concierge.

    Args:
        user_credentials (OAuth2PasswordRequestForm): The login credentials (username and password) of the user.
        current_concierge: The currently authenticated concierge (extracted from the OAuth2 token).
        db (Session): The active database session.

    Returns:
        LoginActivity: An object containing the ID of the newly created activity and the user's details.
    
    Raises:
        HTTPException: If user authentication fails or if the activity cannot be created.
    """
    auth_service = securityService.AuthorizationService(db)
    activity_service = activityService.ActivityService(db)

    user = auth_service.authenticate_user_login(user_credentials.username, user_credentials.password)
    activity = activity_service.create_activity(user.id, current_concierge.id)

    login_activity = LoginActivity(activity_id=activity.id, user=user)
    return login_activity


@router.post("/start-activity/card", response_model=LoginActivity)
def start_card_activity(card_id: CardLogin,
                        current_concierge=Depends(oauth2.get_current_concierge),
                        db: Session = Depends(database.get_db)) -> LoginActivity:
    """
    Start an activity by authenticating a user with a card ID.

    This endpoint allows a concierge to initiate an activity for a user 
    by verifying their card ID. Once authenticated, the system creates an activity 
    for the user and assigns it to the current concierge.

    Args:
        card_id (CardLogin): Object containing the card ID of the user.
        current_concierge: The currently authenticated concierge (extracted from the OAuth2 token).
        db (Session): The active database session.

    Returns:
        LoginActivity: An object containing the ID of the newly created activity and the user's details.
    
    Raises:
        HTTPException: If card authentication fails or if the activity cannot be created.
    """
    auth_service = securityService.AuthorizationService(db)
    activity_service = activityService.ActivityService(db)

    user = auth_service.authenticate_user_card(card_id)
    activity = activity_service.create_activity(user.id, current_concierge.id)

    login_activity = LoginActivity(activity_id=activity.id, user=user)
    return login_activity


@router.post("/refresh", response_model=Token)
def refresh_token(refresh_token: RefreshToken, db: Session = Depends(database.get_db)) -> Token:
    """
    Refresh the access token using a valid refresh token.

    This endpoint allows users to renew their access token by providing 
    a valid refresh token. The system verifies the refresh token and generates a new access token.

    Args:
        refresh_token (RefreshToken): Object containing the refresh token provided during login.
        db (Session): The active database session.

    Returns:
        Token: An object containing the newly generated access token.
    
    Raises:
        HTTPException: If the refresh token is invalid or expired.
    """
    token_service = securityService.TokenService(db)
    token_data = token_service.verify_concierge_token(refresh_token.refresh_token)

    user = db.query(models.User).filter_by(id=token_data.id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    access_token = token_service.create_token(token_data.model_dump(), "access")
    return Token(access_token=access_token, type="bearer")


@router.post("/logout")
def logout(token: str = Depends(oauth2.get_current_concierge_token),
           db: Session = Depends(database.get_db)) -> JSONResponse:
    """
    Log out the concierge by blacklisting their token.

    This endpoint allows a concierge to log out by adding their access token to a blacklist,
    effectively invalidating it for future requests.

    Args:
        token (str): The current access token used by the concierge.
        db (Session): The active database session.

    Returns:
        JSONResponse: A message indicating that the user was logged out successfully.
    
    Raises:
        HTTPException: If the token is invalid or if there is an error during the logout process.
    """
    token_service = securityService.TokenService(db)
    token_data = token_service.verify_concierge_token(token)

    concierge = db.query(models.User).filter_by(id=token_data.id).first()
    if not concierge:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    if token_service.add_token_to_blacklist(token):
        return JSONResponse({"detail": "User logged out successfully"})

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are logged out")
