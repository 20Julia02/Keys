from fastapi import status, Depends, APIRouter
from typing import Sequence, Optional
from app import database, oauth2, schemas
import app.models.user as muser
import app.models.device as mdevice
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/notes",
    tags=['Notes']
)


@router.get("/users", response_model=Sequence[schemas.UserNote])
def get_user_notes_filtered(
        user_id: Optional[int] = None,
        current_concierge: muser.User = Depends(oauth2.get_current_concierge),
        db: Session = Depends(database.get_db)) -> Sequence[schemas.UserNote]:
    """
    It fetches all user-related notes stored in the database. User notes
    typically contain important information associated with users.
    HTTPException: If an error occurs while retrieving the user notes.
    """
    return muser.UserNote.get_user_notes_filter(db, user_id)


@router.get("/users/{note_id}", response_model=schemas.UserNote)
def get_user_notes_id(
        note_id: int,
        current_concierge: muser.User = Depends(oauth2.get_current_concierge),
        db: Session = Depends(database.get_db)) -> schemas.UserNote:
    """
    It fetches all user-related notes stored in the database. User notes
    typically contain important information associated with users.
    HTTPException: If an error occurs while retrieving the user notes.
    """
    return muser.UserNote.get_user_note_id(db, note_id)


@router.post("/users", response_model=schemas.UserNote, status_code=status.HTTP_201_CREATED)
def add_user_note(note_data: schemas.UserNoteCreate,
                  current_concierge: muser.User = Depends(
                      oauth2.get_current_concierge),
                  db: Session = Depends(database.get_db)) -> schemas.UserNote:
    """
    It allows to add a new note to a specific user.
    The note is stored in the database along with the user ID.
    """
    return muser.UserNote.create_user_note(db, note_data)


@router.put("/users/{note_id}", response_model=schemas.UserNote)
def edit_user_note(note_id: int,
                   note_data: schemas.NoteUpdate,
                   current_concierge: muser.User = Depends(
                       oauth2.get_current_concierge),
                   db: Session = Depends(database.get_db)) -> schemas.UserNote:
    """
    Edits a note with the specified ID for a user.
    """
    return muser.UserNote.update_user_note(db, note_id, note_data)


@router.get("/devices", response_model=Sequence[schemas.DeviceNoteOut])
def get_devices_notes_filtered(device_id: Optional[int] = None,
                               current_concierge: muser.User = Depends(oauth2.get_current_concierge),
                               db: Session = Depends(database.get_db)) -> Sequence[schemas.DeviceNoteOut]:
    return mdevice.DeviceNote.get_dev_notes(db, device_id)


@router.get("/devices/{note_id}", response_model=schemas.DeviceNote)
def get_device_notes_id(
        note_id: int,
        current_concierge: muser.User = Depends(oauth2.get_current_concierge),
        db: Session = Depends(database.get_db)) -> schemas.DeviceNote:
    """
    It fetches all user-related notes stored in the database. User notes
    typically contain important information associated with users.
    HTTPException: If an error occurs while retrieving the user notes.
    """
    return mdevice.DeviceNote.get_device_note_id(db, note_id)


@router.post("/devices", response_model=schemas.DeviceNoteOut, status_code=status.HTTP_201_CREATED)
def add_device_note(note_data: schemas.DeviceNote,
                    current_concierge: muser.User = Depends(
                        oauth2.get_current_concierge),
                    db: Session = Depends(database.get_db)) -> schemas.DeviceNoteOut:
    """
    It allows to add a note to a specific operation. The operation is identified
    by its unique ID, and the note is saved in the database.
    """
    return mdevice.DeviceNote.create_dev_note(db, note_data)


@router.put("/devices/{note_id}", response_model=schemas.DeviceNoteOut)
def edit_device_note(note_id: int,
                     note_data: schemas.NoteUpdate,
                     current_concierge: muser.User = Depends(
                         oauth2.get_current_concierge),
                     db: Session = Depends(database.get_db)) -> schemas.DeviceNoteOut:
    """
    Edits a note with the specified ID for a device.
    """
    return mdevice.DeviceNote.update_device_note(db, note_id, note_data)


@router.delete("/devices/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device_note(note_id: int,
                       db: Session = Depends(database.get_db),
                       current_concierge: muser.User = Depends(oauth2.get_current_concierge)):

    return mdevice.DeviceNote.delete_device_note(db, note_id)
