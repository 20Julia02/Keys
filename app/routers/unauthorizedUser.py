from fastapi import status, HTTPException, Depends, APIRouter
from typing import List
from app.schemas import UnauthorizedUser
from app import database, oauth2
import app.models.user as muser
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
    """

    existing_user = db.query(muser.UnauthorizedUser).filter_by(
        email=user.email).first()

    if existing_user:
        if existing_user.name != user.name or existing_user.surname != user.surname:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="User with this email already exists but with different name or surname.")
        return existing_user
    new_user = muser.UnauthorizedUser(**user.model_dump())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.get("/", response_model=List[UnauthorizedUser])
def get_all_unathorized_users(current_concierge=Depends(oauth2.get_current_concierge),
                              db: Session = Depends(database.get_db)) -> List[UnauthorizedUser]:
    """
    Retrieves all unathorized users from the database.
    """
    user = db.query(muser.UnauthorizedUser).all()
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
    """
    user = db.query(muser.UnauthorizedUser).filter(
        muser.UnauthorizedUser.id == id).first()
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
    """
    user = db.query(muser.UnauthorizedUser).filter(
        muser.UnauthorizedUser.id == user_id).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Unauthorized user with id: {user_id} doesn't exist")

    db.delete(user)
    db.commit()

    return True
