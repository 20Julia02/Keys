from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from ..schemas import RefreshToken, Token, LoginConcierge
from ..schemas import CardLogin, UserOut
from .. import database, models, utils, oauth2
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter(
    tags=['Authentication']
)

@router.post("/login", response_model=LoginConcierge)
def login(user_credentials: OAuth2PasswordRequestForm = Depends(), 
          db: Session = Depends(database.get_db)) -> LoginConcierge:
    """
    Authenticates a user and generates JWT tokens for access and refresh.

    Args:
        user_credentials (OAuth2PasswordRequestForm): The user credentials (email and password).
        db (Session): The database session.

    Returns:
        LoginConcierge: The access and refresh tokens.

    Raises:
        HTTPException: If the credentials are invalid or the user is not entitled.
    """
    user = db.query(models.User).filter(
        models.User.email == user_credentials.username).first()

    if not (user and utils.verify_hashed(user_credentials.password,
                                  user.password)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Invalid credentials")
    
    utils.check_if_entitled("concierge", user)

    access_token = oauth2.create_token(
        {"user_id": user.id, "user_role": user.role.value}, "access")
    refresh_token = oauth2.create_token(
        {"user_id": user.id, "user_role": user.role.value}, "refresh")
    return {"access_token": access_token, "type": "bearer", "refresh_token": refresh_token}


@router.post("/card-login", response_model=LoginConcierge)
def card_login(card_id: CardLogin, 
               db: Session = Depends(database.get_db)) -> LoginConcierge:
    """
    Authenticates a user using a card ID and generates JWT tokens for access and refresh.

    Args:
        card_id (CardLogin): The card ID used for login.
        db (Session): The database session.

    Returns:
        LoginConcierge: The access and refresh tokens.

    Raises:
        HTTPException: If the card ID is invalid.
    """
    users = db.query(models.User).filter(
        models.User.card_code.isnot(None)).all()
    if users is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="There is no user in database")
    for user in users:
        if utils.verify_hashed(card_id.card_id, user.card_code):
            utils.check_if_entitled("concierge", user)
            access_token = oauth2.create_token(
                {"user_id": user.id, "user_role": user.role.value}, "access")
            refresh_token = oauth2.create_token(
                {"user_id": user.id, "user_role": user.role.value}, "refresh")
            return {"access_token": access_token, "type": "bearer", "refresh_token": refresh_token}
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Invalid credentials")


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
        HTTPException: If the refresh token is invalid.
    """

    token_data = oauth2.verify_token(refresh_token.refresh_token)

    user = db.query(models.User).filter(models.User.id == token_data.id).first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    access_token = oauth2.create_token(token_data.model_dump(), "access")
    return {"access_token": access_token, "type": "bearer"}


@router.post("/logout")
def logout(token: str = Depends(oauth2.get_current_concierge_token), 
           db: Session = Depends(database.get_db)) -> JSONResponse:
    """
    Logs out the current user by blacklisting their token.

    Args:
        token (str): The JWT token to blacklist.
        db (Session): The database session.

    Returns:
        JSONResponse: A response indicating the logout status.

    Raises:
        HTTPException: If the logout process fails.
    """
    token_data = oauth2.verify_token(token)
    user = db.query(models.User).filter(models.User.id == token_data.id).first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    if utils.add_token_to_blacklist(db, token):
        return JSONResponse({'result': True})
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                        detail="You are logged out")


@router.post("/validate", response_model=UserOut)
def validate(user_credentials: OAuth2PasswordRequestForm = Depends(),
             current_concierge: int = Depends(oauth2.get_current_concierge),
             db: Session = Depends(database.get_db)) -> UserOut:
    """
    Validates the provided user credentials and changes user status to validated.

    Args:
        user_credentials (OAuth2PasswordRequestForm): The user credentials (email and password).
        current_concierge: The current user object (used for authorization).
        db (Session): The database session.

    Returns:
        UserOut: The validated user object.

    Raises:
        HTTPException: If the credentials are invalid.
    """
    user_query = db.query(models.User).filter(
        models.User.email == user_credentials.username)
    user = user_query.first()

    if not (user and utils.verify_hashed(user_credentials.password,
                                  user.password)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Invalid credentials")
    try:
        user_query.update({"is_active": True}, synchronize_session=False)
        db.commit()
        db.refresh(user)
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"An error occurred: {str(e)}")
    return user
