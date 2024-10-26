from fastapi import status, HTTPException, Depends, APIRouter
from typing import List
from app import database, oauth2, schemas
import app.models.user as muser
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/unauthorized-users",
    tags=['Unauthorized users']
)


@router.post("/", response_model=schemas.UnauthorizedUser, status_code=status.HTTP_201_CREATED)
def create_or_get_unauthorized_user(user: schemas.UnauthorizedUserNote,
                                    db: Session = Depends(database.get_db),
                                    current_concierge=Depends(oauth2.get_current_concierge)) -> schemas.UnauthorizedUser:
    """
    Creates a new unauthorized user in the database.
    """
    new_user = muser.UnauthorizedUser.create_or_get_unauthorized_user(db, user.name, user.surname, user.email)
    if user.note:
        note_data = schemas.UserNoteCreate(user_id = new_user.id, note=user.note)
        muser.UserNote.create_user_note(db, note_data)
    return new_user


@router.get("/", response_model=List[ schemas.UnauthorizedUser])
def get_all_unathorized_users(current_concierge=Depends(oauth2.get_current_concierge),
                              db: Session = Depends(database.get_db)) -> List[schemas.UnauthorizedUser]:
    """
    Retrieves all unathorized users from the database.
    """
    return muser.UnauthorizedUser.get_all_unathorized_users(db)


@router.get("/{user_id}", response_model= schemas.UnauthorizedUser)
def get_unathorized_user(user_id: int,
                         current_concierge=Depends(oauth2.get_current_concierge),
                         db: Session = Depends(database.get_db)) ->  schemas.UnauthorizedUser:
    """
    Retrieves an unauthorized user by their ID from the database.
    """
    return muser.UnauthorizedUser.get_unathorized_user(db, user_id)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_unauthorized_user(user_id: int,
                             db: Session = Depends(database.get_db),
                             current_concierge=Depends(oauth2.get_current_concierge)):
    """
    Deletes an unauthorized user by their ID from the database.
    """
    return muser.UnauthorizedUser.delete_unauthorized_user(db, user_id)
