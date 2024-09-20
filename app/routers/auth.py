from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from ..schemas import RefreshToken, Token, LoginConcierge
from ..schemas import CardLogin
from .. import database, models, oauth2
from .. import securityService, activityService

router = APIRouter(
    tags=['Authentication']
)


@router.post("/login", response_model=LoginConcierge)
def login(concierge_credentials: OAuth2PasswordRequestForm = Depends(),
          db: Session = Depends(database.get_db)) -> LoginConcierge:
    """
    Authenticates a cocnierge using their credentials (username and password).

    Args:
        concierge_credentials (OAuth2PasswordRequestForm): Form with login credentials.
        db (Session): Database session.

    Returns:
        LoginConcierge: Object containing generated access and refresh tokens.
    """
    auth_service = securityService.AuthorizationService(db)
    concierge = auth_service.authenticate_user_login(concierge_credentials.username, concierge_credentials.password)
    auth_service.check_if_entitled("concierge", concierge)

    token_service = securityService.TokenService(db)
    return token_service.generate_tokens(concierge.id, concierge.role.value)


@router.post("/card-login", response_model=LoginConcierge)
def card_login(card_id: CardLogin, db: Session = Depends(database.get_db)) -> LoginConcierge:
    """
    Authenticates a concierge using their card ID.

    Args:
        card_id (CardLogin): Object containing the card ID.
        db (Session): Database session.

    Returns:
        LoginConcierge: Object containing generated access and refresh tokens.
    """
    auth_service = securityService.AuthorizationService(db)
    concierge = auth_service.authenticate_user_card(card_id)
    auth_service.check_if_entitled("concierge", concierge)

    token_service = securityService.TokenService(db)
    return token_service.generate_tokens(concierge.id, concierge.role.value)


@router.post("/start_activity", response_model=Token)
def start_login_activity(user_credentials: OAuth2PasswordRequestForm = Depends(),
                         current_concierge=Depends(oauth2.get_current_concierge),
                         db: Session = Depends(database.get_db)) -> Token:
    """
    Starts an activity for a user by authenticating them with credentials.

    Args:
        user_credentials (OAuth2PasswordRequestForm): Form with user login credentials.
        current_concierge: Currently logged-in concierge.
        db (Session): Database session.

    Returns:
        Token: Object containing the generated access token.
    """
    auth_service = securityService.AuthorizationService(db)
    user = auth_service.authenticate_user_login(user_credentials.username, user_credentials.password)

    activity_service = activityService.ActivityService(db)
    activity_id = activity_service.create_activity(user.id, current_concierge.id)

    token_service = securityService.TokenService(db)
    access_token = token_service.create_token({"user_id": user.id, "activity_id": activity_id}, "access")

    return Token(access_token=access_token, type="bearer")


@router.post("/start_activity/card", response_model=Token)
def start_card_activity(card_id: CardLogin,
                        current_concierge=Depends(oauth2.get_current_concierge),
                        db: Session = Depends(database.get_db)) -> Token:
    """
    Starts an activity for a user by authenticating them with a card ID.

    Args:
        card_id (CardLogin): Object containing the card ID.
        current_concierge: Currently logged-in concierge).
        db (Session): Database session.

    Returns:
        Token: Object containing the generated access token.
    """
    auth_service = securityService.AuthorizationService(db)
    user = auth_service.authenticate_user_card(card_id)

    activity_service = activityService.ActivityService(db)
    activity_id = activity_service.create_activity(user.id, current_concierge.id)

    token_service = securityService.TokenService(db)
    access_token = token_service.create_token({"user_id": user.id, "activity_id": activity_id}, "access")

    return Token(access_token=access_token, type="bearer")


@router.post("/refresh", response_model=Token)
def refresh_token(refresh_token: RefreshToken, db: Session = Depends(database.get_db)) -> Token:
    """
    Refreshes the access token using the provided refresh token.

    Args:
        refresh_token (RefreshToken): Object containing the refresh token.
        db (Session): Database session.

    Returns:
        Token: Object containing the new access token.
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
    Logs out the user by adding the token to the blacklist.

    Args:
        token (str): The current user's token.
        db (Session): Database session.

    Returns:
        JSONResponse: Object indicating the result of the logout operation.
    """
    token_service = securityService.TokenService(db)
    token_data = token_service.verify_concierge_token(token)

    concierge = db.query(models.User).filter_by(id=token_data.id).first()
    if not concierge:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    if token_service.add_token_to_blacklist(token):
        return JSONResponse({'result': True})

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are logged out")
