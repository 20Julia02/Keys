from fastapi import status, HTTPException, Depends, APIRouter

from ..schemas import UnauthorizedUserCreate, UnauthorizedUserOut
from .. import database, models, utils, oauth2
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/unauthorizedUsers",
    tags=['UnauthorizedUsers']
)


@router.get("/{id}", response_model=UnauthorizedUserOut)
def get_user(id: int,
             current_user=Depends(oauth2.get_current_user),
             db: Session = Depends(database.get_db)) -> UnauthorizedUserOut:
    """
    Retrieves an unauthorized user by their ID from the database.

    Args:
        id (int): The ID of the unauthorized user.
        current_user: The current user object (used for authorization).
        db (Session): The database session.

    Returns:
        UnauthorizedUserOut: The unauthorized user with the specified ID.

    Raises:
        HTTPException: If the unauthorized user with the specified ID doesn't exist.
    """
    utils.check_if_entitled("concierge", current_user)
    user = db.query(models.UnauthorizedUsers).filter(
        models.UnauthorizedUsers.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Unauthorized user with id: {id} doesn't exist")
    return user


@router.post("/", response_model=UnauthorizedUserOut, status_code=status.HTTP_201_CREATED)
def create_user(user: UnauthorizedUserCreate,
                db: Session = Depends(database.get_db),
                current_user=Depends(oauth2.get_current_user)) -> UnauthorizedUserOut:
    """
    Creates a new unauthorized user in the database.

    Args:
        user (UnauthorizedUserCreate): The data required to create a new unauthorized user.
        db (Session): The database session.
        current_user: The current user object (used for authorization).

    Returns:
        UnauthorizedUserOut: The newly created unauthorized user.
    """
    utils.check_if_entitled("concierge", current_user)
    new_user = models.UnauthorizedUsers(**user.model_dump())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
