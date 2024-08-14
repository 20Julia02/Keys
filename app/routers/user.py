from fastapi import status, Depends, APIRouter, HTTPException
from typing import List
from ..schemas import UserOut, UserCreate
from .. import database, models, utils, oauth2
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/users",
    tags=['Users']
)

@router.get("/", response_model=List[UserOut])
def get_all_users(current_user=Depends(oauth2.get_current_user),
                  db: Session = Depends(database.get_db)) -> List[UserOut]:
    """
    Retrieves all users from the database.

    Args:
        current_user: The current user object (used for authorization).
        db (Session): The database session.

    Returns:
        List[UserOut]: A list of all users in the database.

    Raises:
        HTTPException: If no users are found in the database.
    """
    utils.check_if_entitled("admin", current_user)
    user = db.query(models.User).all()
    if (user is None):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="There is no user in database")
    return user


@router.get("/{id}", response_model=UserOut)
def get_user(id: int,
             current_user=Depends(oauth2.get_current_user),
             db: Session = Depends(database.get_db)) -> UserOut:
    """
    Retrieves a user by their ID from the database.

    Args:
        id (int): The ID of the user.
        current_user: The current user object (used for authorization).
        db (Session): The database session.

    Returns:
        UserOut: The user with the specified ID.

    Raises:
        HTTPException: If the user with the specified ID doesn't exist.
    """
    utils.check_if_entitled("concierge", current_user)
    user = db.query(models.User).filter(models.User.id == id).first()
    if (not user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User with id: {id} doesn't exist")
    return user


@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(user_data: UserCreate,
                db: Session = Depends(database.get_db)) -> UserOut:
    """
    Creates a new user in the database.

    Args:
        user_data (UserCreate): The data required to create a new user.
        db (Session): The database session.

    Returns:
        UserOut: The newly created user.

    Raises:
        HTTPException: If the email is already registered.
    """
    user = db.query(models.User).filter(models.User.email == user_data.email).first()
    if user:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Email is already registered")
    
    hashed_password = utils.hash_password(user_data.password)
    hashed_card_code = utils.hash_password(user_data.card_code)
    user_data.password = hashed_password
    user_data.card_code = hashed_card_code
    new_user = models.User(**user_data.model_dump())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
