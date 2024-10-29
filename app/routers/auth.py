from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from app import database, oauth2, schemas
import app.models.user as muser
from app.services import securityService
import app.models.operation as moperation

router = APIRouter(
    tags=['Authentication']
)


@router.post("/login", response_model=schemas.Token, responses={
    200: {
        "description": "Concierge authorized and tokens generated.",
        "content": {
            "application/json": {
                "example":
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
                    "token_type": "bearer",
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
                }

            }
        },
    },
    403: {
        "description": "Authentication failed due to incorrect login credentials.",
        "content": {
            "application/json": {
                "example": {
                    "invalid_card_code": {
                        "detail": "Invalid credential"
                    },
                    "not_entitled": {
                        "detail": "You cannot perform this operation without the concierge role"
                    }
                }
            }
        }
    },
}
)
def login(concierge_credentials: OAuth2PasswordRequestForm = Depends(),
          db: Session = Depends(database.get_db)) -> schemas.Token:
    """
    Authenticate a concierge using their login credentials (username and password).

    This endpoint allows a concierge to log in by providing valid credentials.
    Upon successful authentication, the system generates and returns an access token
    and a refresh token that can be used for subsequent API requests and token refreshing.
    """
    auth_service = securityService.AuthorizationService(db)
    concierge = auth_service.authenticate_user_login(concierge_credentials.username,
                                                     concierge_credentials.password, "concierge")

    token_service = securityService.TokenService(db)
    return token_service.generate_tokens(concierge.id, concierge.role.value)


@router.post("/login/card", response_model=schemas.Token, responses={
    200: {
        "description": "Concierge authorized and tokens generated.",
        "content": {
            "application/json": {
                "example":
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
                    "token_type": "bearer",
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
                }

            }
        },
    },
    403: {
        "description": "Authentication failed due to incorrect login credentials.",
        "content": {
            "application/json": {
                "example": {
                    "invalid_card_code": {
                        "detail": "Invalid credential"
                    },
                    "not_entitled": {
                        "detail": "You cannot perform this operation without the concierge role"
                    }
                }
            }
        }
    },
}
)
def card_login(card_id: schemas.CardId,
               db: Session = Depends(database.get_db)) -> schemas.Token:
    """
    Authenticate a concierge using their card ID.

    This endpoint allows a concierge to authenticate by providing their card ID.
    Upon successful authentication, the system generates and returns both an access token
    and a refresh token for future API requests and token refreshing.
    """
    auth_service = securityService.AuthorizationService(db)
    concierge = auth_service.authenticate_user_card(card_id, "concierge")

    token_service = securityService.TokenService(db)
    return token_service.generate_tokens(concierge.id, concierge.role.value)


@router.post("/start-session/login", response_model=schemas.IssueReturnSession)
def start_login_session(user_credentials: OAuth2PasswordRequestForm = Depends(),
                        current_concierge=Depends(
                            oauth2.get_current_concierge),
                        db: Session = Depends(database.get_db)) -> schemas.IssueReturnSession:
    """
    Start an session by authenticating a user with credentials (username and password).

    This endpoint allows a concierge to initiate an session for a user by verifying
    their login credentials. Once authenticated, the system creates an session for
    the user and assigns it to the current concierge.
    """
    auth_service = securityService.AuthorizationService(db)

    user = auth_service.authenticate_user_login(
        user_credentials.username, user_credentials.password, "employee")
    return moperation.IssueReturnSession.create_session(db, user.id, current_concierge.id)


@router.post("/start-session/card", response_model=schemas.IssueReturnSession)
def start_card_session(card_id: schemas.CardId,
                       current_concierge=Depends(oauth2.get_current_concierge),
                       db: Session = Depends(database.get_db)) -> schemas.IssueReturnSession:
    """
    Start an session by authenticating a user with a card ID.

    This endpoint allows a concierge to initiate an session for a user
    by verifying their card ID. Once authenticated, the system creates an session
    for the user and assigns it to the current concierge.
    """
    auth_service = securityService.AuthorizationService(db)
    user = auth_service.authenticate_user_card(card_id, "employee")
    return moperation.IssueReturnSession.create_session(db, user.id, current_concierge.id)


@router.post("/start-session/unauthorized", response_model=schemas.IssueReturnSession)
def start_unauthorized_session(unauthorized_id: int,
                               current_concierge=Depends(
                                   oauth2.get_current_concierge),
                               db: Session = Depends(database.get_db)) -> schemas.IssueReturnSession:
    return moperation.IssueReturnSession.create_session(db, unauthorized_id, current_concierge.id)


@router.post("/refresh", response_model=schemas.Token)
def refresh_token(refresh_token: schemas.RefreshToken, db: Session = Depends(database.get_db)) -> schemas.Token:
    """
    Refresh the access token using a valid refresh token.

    This endpoint allows users to renew their access token by providing
    a valid refresh token. The system verifies the refresh token and generates a new access token.
    """
    token_service = securityService.TokenService(db)
    token_data = token_service.verify_concierge_token(
        refresh_token.refresh_token)

    user = db.query(muser.User).filter_by(id=token_data.id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    return token_service.generate_tokens(user.id, user.role.value)


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

    concierge = db.query(muser.User).filter_by(id=token_data.id).first()
    if not concierge:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    if token_service.add_token_to_blacklist(token):
        return JSONResponse({"detail": "User logged out successfully"})

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                        detail="You are logged out")
