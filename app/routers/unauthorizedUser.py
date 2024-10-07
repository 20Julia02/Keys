from fastapi import status, HTTPException, Depends, APIRouter
from typing import List
from app.schemas import UnauthorizedUserCreate, UnauthorizedUserOut
from app import database, models, oauth2
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/unauthorized-users",
    tags=['Unauthorized users']
)


@router.get("/", response_model=List[UnauthorizedUserOut])
def get_all_unathorized_users(current_concierge=Depends(oauth2.get_current_concierge),
                              db: Session = Depends(database.get_db)) -> List[UnauthorizedUserOut]:
    """
    Retrieves all unathorized users from the database.

    Args:
        current_concierge: The current user object (used for authorization).
        db (Session): The database session.

    Returns:
        List[UnauthorizedUserOut]: A list of all unauthorized users in the database.

    Raises:
        HTTPException: If no unauthorized users are found in the database.
    """
    user = db.query(models.UnauthorizedUser).all()
    if (user is None):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="There is no unauthorized user in database")
    return user


@router.get("/{id}", response_model=UnauthorizedUserOut)
def get_unathorized_user(id: int,
                         current_concierge=Depends(oauth2.get_current_concierge),
                         db: Session = Depends(database.get_db)) -> UnauthorizedUserOut:
    """
    Retrieves an unauthorized user by their ID from the database.

    Args:
        id (int): The ID of the unauthorized user.
        current_concierge: The current user object (used for authorization).
        db (Session): The database session.

    Returns:
        UnauthorizedUserOut: The unauthorized user with the specified ID.

    Raises:
        HTTPException: If the unauthorized user with the specified ID doesn't exist.
    """
    user = db.query(models.UnauthorizedUser).filter(
        models.UnauthorizedUser.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Unauthorized user with id: {id} doesn't exist")
    return user


@router.post("/", response_model=UnauthorizedUserOut, status_code=status.HTTP_201_CREATED)
def create_unauthorized_user(user: UnauthorizedUserCreate,
                             db: Session = Depends(database.get_db),
                             current_concierge=Depends(oauth2.get_current_concierge)) -> UnauthorizedUserOut:
    """
    Creates a new unauthorized user in the database.

    Args:
        user (UnauthorizedUserCreate): The data required to create a new unauthorized user.
        db (Session): The database session.
        current_concierge: The current user object (used for authorization).

    Returns:
        UnauthorizedUserOut: The newly created unauthorized user.
    """

    new_user = models.UnauthorizedUser(**user.model_dump())
    db.add(new_user)
    db.commit()
    return new_user


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_unauthorized_user(id: int,
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
        models.UnauthorizedUser.id == id).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Unauthorized user with id: {id} doesn't exist")

    db.delete(user)
    db.commit()

    return True
