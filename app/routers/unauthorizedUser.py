from fastapi import status, HTTPException, Depends, APIRouter
from typing import List
from app.schemas import UnauthorizedUser
from app import database, models, oauth2
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/unauthorized-users",
    tags=['Unauthorized users']
)


@router.post("/", response_model=UnauthorizedUser, status_code=status.HTTP_201_CREATED)
def create_or_get_unauthorized_user(user: UnauthorizedUser,
                                    db: Session = Depends(database.get_db),
                                    current_concierge=Depends(oauth2.get_current_concierge)) -> UnauthorizedUser:
    """
    Creates a new unauthorized user in the database.

    Args:
        user (UnauthorizedUser): The data required to create a new unauthorized user.
        db (Session): The database session.
        current_concierge: The current user object (used for authorization).

    Returns:
        UnauthorizedUser: The newly created unauthorized user.
    """

    existing_user = db.query(models.UnauthorizedUser).filter_by(
        email=user.email).first()

    if existing_user:
        if existing_user.name != user.name or existing_user.surname != user.surname:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="User with this email already exists but with different name or surname.")
        return existing_user
    new_user = models.UnauthorizedUser(**user.model_dump())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.get("/", response_model=List[UnauthorizedUser])
def get_all_unathorized_users(current_concierge=Depends(oauth2.get_current_concierge),
                              db: Session = Depends(database.get_db)) -> List[UnauthorizedUser]:
    """
    Retrieves all unathorized users from the database.

    Args:
        current_concierge: The current user object (used for authorization).
        db (Session): The database session.

    Returns:
        List[UnauthorizedUser]: A list of all unauthorized users in the database.

    Raises:
        HTTPException: If no unauthorized users are found in the database.
    """
    user = db.query(models.UnauthorizedUser).all()
    if (user is None):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="There is no unauthorized user in database")
    return user


@router.get("/{id}", response_model=UnauthorizedUser)
def get_unathorized_user(id: int,
                         current_concierge=Depends(
                             oauth2.get_current_concierge),
                         db: Session = Depends(database.get_db)) -> UnauthorizedUser:
    """
    Retrieves an unauthorized user by their ID from the database.

    Args:
        id (int): The ID of the unauthorized user.
        current_concierge: The current user object (used for authorization).
        db (Session): The database session.

    Returns:
        UnauthorizedUser: The unauthorized user with the specified ID.

    Raises:
        HTTPException: If the unauthorized user with the specified ID doesn't exist.
    """
    user = db.query(models.UnauthorizedUser).filter(
        models.UnauthorizedUser.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Unauthorized user with id: {id} doesn't exist")
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_unauthorized_user(user_id: int,
                             db: Session = Depends(database.get_db),
                             current_concierge=Depends(oauth2.get_current_concierge)):
    """
    Deletes an unauthorized user by their ID from the database.

    Args:
        id (int): The ID of the unauthorized user to delete.
        db (Session): The database session.
        current_concierge: The current user object (used for authorization).

    Returns:
        HTTP 204 NO CONTENT: If the user was successfully deleted.

    Raises:
        HTTPException: If the unauthorized user with the specified ID doesn't exist.
    """
    user = db.query(models.UnauthorizedUser).filter(
        models.UnauthorizedUser.id == user_id).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Unauthorized user with id: {user_id} doesn't exist")

    db.delete(user)
    db.commit()

    return True
