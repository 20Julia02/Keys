from fastapi import status, HTTPException, Depends, APIRouter

from ..schemas import UnauthorizedUserCreate, UnauthorizedUserOut
from .. import database, models, oauth2
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/unauthorized_users",
    tags=['unauthorized_users']
)


@router.get("/{id}", response_model=UnauthorizedUserOut)
def get_user(id: int,
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
    user = db.query(models.unauthorized_users).filter(
        models.unauthorized_users.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Unauthorized user with id: {id} doesn't exist")
    return user


@router.post("/", response_model=UnauthorizedUserOut, status_code=status.HTTP_201_CREATED)
def create_user(user: UnauthorizedUserCreate,
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
    user.id_concierge_who_accepted = current_concierge.id
    new_user = models.unauthorized_users(**user.model_dump())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
