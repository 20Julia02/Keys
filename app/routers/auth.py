from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from app import database, oauth2, schemas
import app.models.user as muser
from app.services import securityService
from app.config import logger
from fastapi import Response
from fastapi.responses import JSONResponse

router = APIRouter(
    tags=['Authentication']
)


@router.post("/login", responses={
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
def login(response: Response,
          concierge_credentials: OAuth2PasswordRequestForm = Depends(),
          db: Session = Depends(database.get_db),
          ):
    """
    Authenticate a concierge using their login credentials.

    This endpoint verifies the provided username and password against the database. 
    If the credentials are valid and the user has the "concierge" role, 
    an access token is generated and set as a cookie in the response.
    """
    logger.info(f"POST request to login user by login and password")

    auth_service = securityService.AuthorizationService(db)
    concierge = auth_service.authenticate_user_login(concierge_credentials.username,
                                                     concierge_credentials.password, "concierge")

    oauth2.set_access_token_cookie(response, concierge.id, concierge.role.value, db)
    return



@router.post("/login/card", response_model=schemas.AccessToken, responses={
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
def card_login(response: Response,
               card_code: schemas.CardId,
               db: Session = Depends(database.get_db)) -> schemas.AccessToken:
    """
    AAuthenticate a concierge using their card ID.

    This endpoint allows a concierge to log in by providing their card ID. 
    If the card ID is valid and the user has the "concierge" role, 
    an access token is generated, set as a cookie, and returned in the response.
    """
    logger.info(f"POST request to login user by card")
    auth_service = securityService.AuthorizationService(db)
    concierge = auth_service.authenticate_user_card(card_code, "concierge")

    access_token = oauth2.set_access_token_cookie(response, concierge.id, concierge.role.value, db)
    
    return schemas.AccessToken(access_token=access_token)



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
def get_current_user(current_concierge: muser.User = Depends(oauth2.get_current_concierge),
                     db: Session = Depends(database.get_db)) -> schemas.UserOut:
    """
    Retrieve the details of the currently authenticated user.

    This endpoint uses the provided access token to identify the currently logged-in user.
    It fetches and returns the user's information from the database.
    """
    logger.info(f"GET request to retrieve current user information")

    return current_concierge

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
def logout(response: Response,
           access_token: str = Depends(oauth2.get_current_concierge_token),
           db: Session = Depends(database.get_db)) -> JSONResponse:
    """
    Log out the currently authenticated user.

    This endpoint blacklists the user's current access token to prevent further usage. 
    It also removes the refresh token cookie from the response.
    """
    logger.info(f"POST request to logout user")
    token_service = securityService.TokenService(db)

    token_service.add_token_to_blacklist(access_token)

    response.delete_cookie("refresh_token")

    return JSONResponse({"detail": "User logged out successfully"})
