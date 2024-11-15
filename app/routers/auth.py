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
    403: {
        "description": "Authentication failed due to incorrect login credentials.",
        "content": {
            "application/json": {
                "example": {
                    "invalid_card_code": {
                        "detail": "Invalid credentials"
                    },
                    "not_entitled": {
                        "detail": "You cannot perform this operation without the employee role"
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
    403: {
        "description": "Authentication failed due to incorrect login credentials.",
        "content": {
            "application/json": {
                "example": {
                    "invalid_card_code": {
                        "detail": "Invalid credentials"
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



@router.post("/refresh", response_model=schemas.Token, responses={
    401: {
        "description": "Invalid or expired refresh token.",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Invalid token"
                }
            }
        }
    },
})
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


@router.post("/logout", responses={
    401: {
        "description": "Invalid or expired refresh token.",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Invalid token"
                }
            }
        }
    },
    403: {
        "description": "User is already logged out.",
        "content": {
            "application/json": {
                "example": {
                    "detail": "You are logged out"
                }
            }
        }
    },
})
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
