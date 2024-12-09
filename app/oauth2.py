from app import database
import app.models.user as muser
from app.services.securityService import AuthorizationService
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='login')


def get_current_concierge(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(database.get_db)
) -> muser.User:
    auth_service = AuthorizationService(db)
    return auth_service.get_current_concierge(token)


def get_current_concierge_token(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(database.get_db)
) -> str:
    auth_service = AuthorizationService(db)
    return auth_service.get_current_concierge_token(token)