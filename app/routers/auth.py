from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from app import database, oauth2, schemas
import app.models.user as muser
from app.services import securityService
from app.config import logger
from fastapi.responses import JSONResponse
from fastapi import Request

router = APIRouter(
    tags=['Authentication']
)


@router.post("/login", response_model=schemas.Token, responses={
    403: {
        "description": "Credentials are invalid or the user does not have the required role.",
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
          db: Session = Depends(database.get_db),
          ) -> schemas.Token:
    """
    Authenticate a concierge using their login credentials (username and password).
    """
    logger.info(f"POST request to login user by login and password")

    auth_service = securityService.AuthorizationService(db)
    concierge = auth_service.authenticate_user_login(concierge_credentials.username,
                                                     concierge_credentials.password, "concierge")

    token_service = securityService.TokenService(db)
    tokens = token_service.generate_tokens(concierge.id, concierge.role.value)
    return tokens


@router.post("/login/card", response_model=schemas.Token, responses={
    403: {
        "description": "Credentials are invalid or the user does not have the required role.",
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
def card_login(card_code: schemas.CardId,
               db: Session = Depends(database.get_db)) -> schemas.Token:
    """
    Authenticate a concierge using their card ID.
    This endpoint allows a concierge to authenticate by providing their card ID.
    Upon successful authentication, the system generates and returns both an access token
    and a refresh token for future API requests and token refreshing.
    """
    logger.info(f"POST request to login user by card")
    auth_service = securityService.AuthorizationService(db)
    concierge = auth_service.authenticate_user_card(card_code, "concierge")

    token_service = securityService.TokenService(db)
    tokens = token_service.generate_tokens(concierge.id, concierge.role.value)
    return tokens


@router.get("/concierge", response_model=schemas.UserOut, responses={
    401: {
        "description": "Token is invalid or is missing required data.",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Invalid token"
                }
            }
        },
    },
    404: {
        "description": "No user with the given ID exists in the database.",
        "content": {
            "application/json": {
                "example": {
                    "user_not_found":{
                        "detail": "User doesn't exist"
                    },
                    "missing_data":{
                        "detail": "Invalid token"
                    }
                }
            }
        },
    },
})
def get_current_user(token: str = Depends(oauth2.get_current_concierge_token),
                     db: Session = Depends(database.get_db)) -> schemas.UserOut:
    """
    Get the current logged-in user based on the provided token.
    This endpoint returns the details of the user who is currently authenticated.
    It verifies the provided token and retrieves the user's data.
    """
    logger.info(f"GET request to retrieve current user information")

    token_service = securityService.TokenService(db)
    token_data = token_service.verify_concierge_token(token)
    if token_data.id is None:
        logger.warning(f"Token is missing user_id.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = muser.User.get_user_id(db, token_data.id)
    return user


@router.post("/refresh", response_model=schemas.AccessToken, responses={
    401: {
        "description": "Token is invalid or is missing required data.",
        "content": {
            "application/json": {
                "example": {
                    "missing_data":{"detail": "Invalid token"},
                    "invalid_token":{"detail": "Failed to verify token"}
                }
            }
        },
    },
})
def refresh_token(request: Request, 
                  db: Session = Depends(database.get_db)) -> schemas.AccessToken:
    """
    Refresh the access token using a valid refresh token.
    """
    logger.info(f"POST request to refresh tokens")
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing")
    token_service = securityService.TokenService(db)
    auth_service = securityService.AuthorizationService(db)

    token_data = auth_service.get_current_concierge(refresh_token)
    access_token = token_service.create_token({"user_id": token_data.id, "user_role": token_data.role.value}, "access")
    return schemas.AccessToken(access_token=access_token)

@router.post("/logout", responses={
    401: {
        "description": "Token is invalid or is missing required data.",
        "content": {
            "application/json": {
                "example": {
                    "missing_data":{"detail": "Invalid token"},
                    "invalid_token":{"detail": "Failed to verify token"}
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
def logout(refresh_token: schemas.RefreshToken, 
           access_token: str = Depends(oauth2.get_current_concierge_token),
           db: Session = Depends(database.get_db)) -> JSONResponse:
    """
    Log out the concierge by blacklisting their tokens.
    """
    logger.info(f"POST request to logout user")
    token_service = securityService.TokenService(db)

    token_service.add_token_to_blacklist(access_token)
    token_service.add_token_to_blacklist(refresh_token.refresh_token)

    return JSONResponse({"detail": "User logged out successfully"})