from app import database
import app.models.user as muser
from app.services.securityService import AuthorizationService
from fastapi import Depends, Request, HTTPException, status, Response
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.services import securityService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='login')


def get_current_concierge(
    request: Request,
    db: Session = Depends(database.get_db)
) -> muser.User:
    token = request.cookies.get("access_token")
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    auth_service = AuthorizationService(db)
    return auth_service.get_current_concierge(token)


def get_current_concierge_token(
    request: Request,
    db: Session = Depends(database.get_db)
) -> str:
    token = request.cookies.get("access_token")
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    auth_service = AuthorizationService(db)
    return auth_service.get_current_concierge_token(token)

def set_access_token_cookie(response: Response, 
                            user_id: int, 
                            user_role: str, 
                            db: Session)->str:
    token_service = securityService.TokenService(db)
    access_token = token_service.create_token({"user_id": user_id, "user_role": user_role}, "access")

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # zmienic na True
        max_age=86400,
        samesite="strict"
    )
    return access_token