from fastapi import Depends, APIRouter
from typing import List
from app.schemas import UserOut
from app import database, oauth2
from app.services import userService
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/users",
    tags=['Users']
)


@router.get("/", response_model=List[UserOut])
def get_all_users(current_concierge=Depends(oauth2.get_current_concierge),
                  db: Session = Depends(database.get_db)) -> List[UserOut]:
    """
    Retrieves all users from the database.

    Args:
        current_concierge: The current user object (used for authorization).
        db (Session): The database session.

    Returns:
        List[UserOut]: A list of all users in the database.

    Raises:
        HTTPException: If no users are found in the database.
    """
    user_service = userService.UserService(db)
    return user_service.get_all_users()


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int,
             current_concierge=Depends(oauth2.get_current_concierge),
             db: Session = Depends(database.get_db)) -> UserOut:
    """
    Retrieves a user by their ID from the database.

    Args:
        id (int): The ID of the user.
        current_concierge: The current user object (used for authorization).
        db (Session): The database session.

    Returns:
        UserOut: The user with the specified ID.

    Raises:
        HTTPException: If the user with the specified ID doesn't exist.
    """
    user_service = userService.UserService(db)
    return user_service.get_user_id(user_id)
