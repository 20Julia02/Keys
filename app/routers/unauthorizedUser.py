from fastapi import status, Depends, APIRouter, Response
from typing import Sequence
from app import database, oauth2, schemas
import app.models.user as muser
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/unauthorized-users",
    tags=['Unauthorized users']
)

@router.post("/", response_model=schemas.UnauthorizedUserOut)
def create_or_get_unauthorized_user(user: schemas.UnauthorizedUserNote,
                                    response: Response,
                                    db: Session = Depends(database.get_db),
                                    current_concierge: muser.User = Depends(oauth2.get_current_concierge)
                                    ) -> schemas.UnauthorizedUserOut:
    """
    Creates a new unauthorized user in the database or returns an existing one.
    """
    new_user, created = muser.UnauthorizedUser.create_or_get_unauthorized_user(
        db, user.name, user.surname, user.email)
    
    if created:
        response.status_code = status.HTTP_201_CREATED
    else:
        response.status_code = status.HTTP_200_OK

    if user.note:
        note_data = schemas.UserNoteCreate(user_id=new_user.id, note=user.note)
        muser.UserNote.create_user_note(db, note_data)
        
    return new_user


@router.get("/", response_model=Sequence[schemas.UnauthorizedUserOut])
def get_all_unathorized_users(current_concierge: muser.User = Depends(oauth2.get_current_concierge),
                              db: Session = Depends(database.get_db)) -> Sequence[schemas.UnauthorizedUserOut]:
    """
    Retrieves all unathorized users from the database.
    """
    return muser.UnauthorizedUser.get_all_unathorized_users(db)


@router.get("/{user_id}", response_model=schemas.UnauthorizedUserOut)
def get_unathorized_user(user_id: int,
                         current_concierge: muser.User = Depends(
                             oauth2.get_current_concierge),
                         db: Session = Depends(database.get_db)) -> schemas.UnauthorizedUserOut:
    """
    Retrieves an unauthorized user by their ID from the database.
    """
    return muser.UnauthorizedUser.get_unathorized_user(db, user_id)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_unauthorized_user(user_id: int,
                             db: Session = Depends(database.get_db),
                             current_concierge: muser.User = Depends(oauth2.get_current_concierge)):
    """
    Deletes an unauthorized user by their ID from the database.
    """
    return muser.UnauthorizedUser.delete_unauthorized_user(db, user_id)
