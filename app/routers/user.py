from fastapi import Depends, APIRouter
from typing import List
from app.schemas import UserOut
from app import database, oauth2
from sqlalchemy.orm import Session
import app.models.user as muser

router = APIRouter(
    prefix="/users",
    tags=['Users']
)


@router.get("/", response_model=List[UserOut])
def get_all_users(current_concierge=Depends(oauth2.get_current_concierge),
                  db: Session = Depends(database.get_db)) -> List[UserOut]:
    """
    Retrieves all users from the database.
    """
    return muser.User.get_all_users(db)


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int,
             current_concierge=Depends(oauth2.get_current_concierge),
             db: Session = Depends(database.get_db)) -> UserOut:
    """
    Retrieves a user by their ID from the database.
    """
    return muser.User.get_user_id(db, user_id)
