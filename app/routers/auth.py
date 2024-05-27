from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse

from ..schemas.token import Token, CreateRefreshToken
from .. import database, models, utils, oauth2
from ..utils import add_token_to_blacklist

router = APIRouter(
    tags=['Authentication']
)


@router.post("/login", response_model=CreateRefreshToken)
def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):

    user = db.query(models.User).filter(
        models.User.email == user_credentials.username).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Invalid credentials")

    if not utils.verify(user_credentials.password,
                        user.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Invalid credentials")

    access_token = oauth2.create_access_token(
        {"user_id": user.id, "user_role": user.role.value})
    refresh_token = oauth2.create_refresh_token(
        {"user_id": user.id, "user_role": user.role.value})
    return {"access_token": access_token, "type": "bearer", "refresh_token": refresh_token}


@router.post("/refresh", response_model=Token)
def refresh_token(refresh_token: str, db: Session = Depends(database.get_db)):
    token_data = oauth2.verify_token(refresh_token,
                                     HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                                   detail="Invalid credentials"))
    access_token = oauth2.create_access_token(token_data.model_dump())
    return {"access_token": access_token, "type": "bearer"}


@router.post("/logout")
async def logout(token: str = Depends(oauth2.get_current_user_token), db: Session = Depends(database.get_db)):
    if add_token_to_blacklist(db, token):
        return JSONResponse({'result': True})
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                        detail="You are logged out")
