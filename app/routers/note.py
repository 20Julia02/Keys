from fastapi import status, Depends, APIRouter, HTTPException
from typing import List
from app import database, oauth2, schemas, models
from app.services import noteService
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/notes",
    tags=['Notes']
)


@router.get("/users", response_model=List[schemas.UserNote])
def get_all_user_notes(
        current_concierge=Depends(oauth2.get_current_concierge),
        db: Session = Depends(database.get_db)) -> List[schemas.UserNote]:
    """
    It fetches all user-related notes stored in the database. User notes
    typically contain important information associated with users.
    HTTPException: If an error occurs while retrieving the user notes.
    """
    note_service = noteService.NoteService(db)
    return note_service.get_all_user_notes()


@router.get("/users/{user_id}", response_model=List[schemas.UserNote])
def get_user_note_id(user_id: int,
                     current_concierge=Depends(oauth2.get_current_concierge),
                     db: Session = Depends(database.get_db)) -> List[schemas.UserNote]:
    """
    It allows to fetch all notes associated with a specific user
    based on the user ID.
    """
    note_service = noteService.NoteService(db)
    return note_service.get_user_note_by_id(user_id)


@router.post("/users", response_model=schemas.UserNote, status_code=status.HTTP_201_CREATED)
def add_user_note(note_data: schemas.UserNoteCreate,
                  current_concierge=Depends(oauth2.get_current_concierge),
                  db: Session = Depends(database.get_db)) -> schemas.UserNote:
    """
    It allows to add a new note to a specific user.
    The note is stored in the database along with the user ID.
    """
    note_service = noteService.NoteService(db)
    return note_service.create_user_note(note_data)


@router.put("/users/{note_id}", response_model=schemas.UserNote)
def edit_user_note(note_id: int,
                   note_data: schemas.NoteUpdate,
                   current_concierge=Depends(oauth2.get_current_concierge),
                   db: Session = Depends(database.get_db)) -> schemas.UserNote:
    """
    Edits a note with the specified ID for a user.
    """
    note_service = noteService.NoteService(db)
    return note_service.update_user_note(note_id, note_data)


@router.get("/devices", response_model=List[schemas.DeviceNoteOut])
def get_all_devices_notes(
        current_concierge=Depends(oauth2.get_current_concierge),
        db: Session = Depends(database.get_db)) -> List[schemas.DeviceNoteOut]:
    note_service = noteService.NoteService(db)
    return note_service.get_dev_notes()


@router.get("/devices/{device_id}", response_model=List[schemas.DeviceNoteOut])
def get_device_notes_id(
        device_id: int,
        current_concierge=Depends(oauth2.get_current_concierge),
        db: Session = Depends(database.get_db)) -> List[schemas.DeviceNoteOut]:
    note_service = noteService.NoteService(db)
    return note_service.get_dev_notes_id(device_id)


@router.post("/devices", response_model=schemas.DeviceNoteOut, status_code=status.HTTP_201_CREATED)
def add_device_note(note_data: schemas.DeviceNote,
                    current_concierge=Depends(oauth2.get_current_concierge),
                    db: Session = Depends(database.get_db)) -> schemas.DeviceNoteOut:
    """
    It allows to add a note to a specific operation. The operation is identified
    by its unique ID, and the note is saved in the database.
    """

    note_service = noteService.NoteService(db)
    return note_service.create_dev_note(note_data)


@router.put("/devices/{note_id}", response_model=schemas.DeviceNoteOut)
def edit_device_note(note_id: int,
                     note_data: schemas.NoteUpdate,
                     current_concierge=Depends(oauth2.get_current_concierge),
                     db: Session = Depends(database.get_db)) -> schemas.DeviceNoteOut:
    """
    Edits a note with the specified ID for a device.
    """
    note_service = noteService.NoteService(db)
    return note_service.update_device_note(note_id, note_data)


@router.delete("/devices/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device_note(note_id: int,
                       db: Session = Depends(database.get_db),
                       current_concierge=Depends(oauth2.get_current_concierge)):
    note = db.query(models.DeviceNote).filter(
        models.DeviceNote.id == note_id).first()

    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Note with id: {note_id} doesn't exist")

    db.delete(note)
    db.commit()
